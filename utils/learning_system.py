"""
CASS - Learning System Orchestrator
Manages autonomous self-learning through random sampling and VLM verification
"""
import os
import random
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

from database import db
from models import (
    VerificationLog, ModelPerformance, TrainingQueue, ModelVersion,
    DetectionLog
)
from config import (
    LEARNING_ENABLED, RANDOM_SAMPLING_ENABLED, SAMPLING_RATE,
    SAMPLING_MIN_INTERVAL_SECONDS, VERIFICATION_IMAGE_DIR,
    MIN_VERIFIED_SAMPLES_FOR_RETRAINING, AUTO_THRESHOLD_ADJUSTMENT,
    THRESHOLD_ADJUSTMENT_WINDOW, MIN_VERIFIED_SAMPLES_FOR_ADJUSTMENT,
    THRESHOLD_STEP_SIZE, DETECTION_MODELS
)

logger = logging.getLogger(__name__)


class LearningSystem:
    """Central orchestrator for autonomous self-learning"""
    
    def __init__(self, flask_app=None):
        """
        Initialize learning system
        
        Args:
            flask_app: Flask app instance for database operations
        """
        self.app = flask_app
        self.enabled = LEARNING_ENABLED and RANDOM_SAMPLING_ENABLED
        self.sampling_rate = SAMPLING_RATE
        self.last_sample_time = {}  # Track last sample time per camera
        self.verification_queue = []  # Queue of detections awaiting VLM verification
        
        logger.info(f"Learning system initialized (enabled={self.enabled}, sampling_rate={self.sampling_rate:.1%})")
    
    def should_sample_detection(self, camera_id: int, model_name: str) -> bool:
        """
        Determine if a detection should be randomly sampled
        
        Args:
            camera_id: Camera ID
            model_name: Model name
        
        Returns:
            True if detection should be sampled (~5% of time)
        """
        if not self.enabled:
            return False
        
        # Check minimum interval
        key = f"{camera_id}_{model_name}"
        last_time = self.last_sample_time.get(key, datetime.min)
        time_since_last = (datetime.now() - last_time).total_seconds()
        
        if time_since_last < SAMPLING_MIN_INTERVAL_SECONDS:
            return False
        
        # Random sampling with configured rate
        if random.random() < self.sampling_rate:
            self.last_sample_time[key] = datetime.now()
            return True
        
        return False
    
    def queue_for_vlm_verification(
        self,
        detection_log_id: int,
        image_path: str,
        model_name: str,
        detection_data: Dict = None
    ):
        """
        Add sampled detection to VLM verification queue
        
        Args:
            detection_log_id: Detection log ID
            image_path: Path to saved detection image
            model_name: Model name
            detection_data: Optional detection metadata (count, confidence, etc.)
        """
        self.verification_queue.append({
            'detection_log_id': detection_log_id,
            'image_path': image_path,
            'model_name': model_name,
            'detection_data': detection_data or {},
            'queued_at': datetime.now()
        })
        
        logger.info(f"Queued detection {detection_log_id} for VLM verification (queue size: {len(self.verification_queue)})")
    
    def get_verification_queue(self, limit: int = None) -> List[Dict]:
        """
        Get pending verifications from queue
        
        Args:
            limit: Maximum number to return
        
        Returns:
            List of verification items
        """
        if limit:
            return self.verification_queue[:limit]
        return self.verification_queue.copy()
    
    def clear_verification_queue(self, count: int = None):
        """
        Remove items from verification queue
        
        Args:
            count: Number of items to remove from front, or None for all
        """
        if count:
            self.verification_queue = self.verification_queue[count:]
        else:
            self.verification_queue.clear()
    
    def process_vlm_verification(
        self,
        detection_log_id: int,
        vlm_result: Dict,
        flask_app=None
    ):
        """
        Process VLM verification result and store in database
        
        Args:
            detection_log_id: Detection log ID
            vlm_result: Result from VLMVerifier.verify_detection()
            flask_app: Flask app for database context
        """
        app = flask_app or self.app
        if not app:
            logger.error("No Flask app available for database operations")
            return
        
        with app.app_context():
            try:
                # Create verification log entry
                verification = VerificationLog(
                    detection_log_id=detection_log_id,
                    verification_source='VLM_AUTO',
                    verification_result=vlm_result['verification_result'],
                    confidence_rating=vlm_result['confidence'],
                    vlmmodel_used=vlm_result['vlm_model_used'],
                    vlm_response=vlm_result['vlm_response'],
                    image_path=vlm_result.get('image_path'),
                    sampled_randomly=True
                )
                
                db.session.add(verification)
                db.session.commit()
                
                logger.info(f"Stored VLM verification for detection {detection_log_id}: {vlm_result['verification_result']}")
                
                # Update performance metrics
                self._update_performance_metrics(detection_log_id, vlm_result)
                
            except Exception as e:
                logger.error(f"Error processing VLM verification: {str(e)}")
                db.session.rollback()
    
    def _update_performance_metrics(self, detection_log_id: int, vlm_result: Dict):
        """Update daily performance metrics with verification result"""
        try:
            # Get detection info
            detection = DetectionLog.query.get(detection_log_id)
            if not detection:
                return
            
            today = datetime.now().date()
            model_name = detection.model_name
            
            # Get or create performance entry for today
            perf = ModelPerformance.query.filter_by(
                model_name=model_name,
                date=today
            ).first()
            
            if not perf:
                perf = ModelPerformance(
                    model_name=model_name,
                    date=today,
                    total_detections=0,
                    verified_detections=0,
                    true_positives=0,
                    false_positives=0
                )
                db.session.add(perf)
            
            # Update counts
            perf.verified_detections += 1
            
            if vlm_result['verification_result'] == 'CORRECT':
                perf.true_positives += 1
            elif vlm_result['verification_result'] == 'INCORRECT':
                perf.false_positives += 1
            
            # Calculate accuracy
            total_verified = perf.true_positives + perf.false_positives
            if total_verified > 0:
                perf.accuracy_rate = perf.true_positives / total_verified
            
            # Store current threshold
            model_config = DETECTION_MODELS.get(model_name, {})
            perf.threshold_used = model_config.get('confidence_threshold', 0.5)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
            db.session.rollback()
    
    def analyze_performance(self, model_name: str, days: int = 7, flask_app=None) -> Dict:
        """
        Analyze model performance over time
        
        Args:
            model_name: Model to analyze
            days: Number of days to analyze
            flask_app: Flask app for database context
        
        Returns:
            Performance analysis dict
        """
        app = flask_app or self.app
        if not app:
            return {}
        
        with app.app_context():
            cutoff_date = (datetime.now() - timedelta(days=days)).date()
            
            perfs = ModelPerformance.query.filter(
                ModelPerformance.model_name == model_name,
                ModelPerformance.date >= cutoff_date
            ).order_by(ModelPerformance.date.asc()).all()
            
            if not perfs:
                return {'model_name': model_name, 'data_available': False}
            
            # Calculate aggregates
            total_verified = sum(p.verified_detections for p in perfs)
            total_tp = sum(p.true_positives for p in perfs)
            total_fp = sum(p.false_positives for p in perfs)
            
            accuracy = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
            
            return {
                'model_name': model_name,
                'data_available': True,
                'period_days': days,
                'total_verified': total_verified,
                'accuracy': accuracy,
                'daily_metrics': [p.to_dict() for p in perfs],
                'trend': self._calculate_trend(perfs)
            }
    
    def _calculate_trend(self, perfs: List) -> str:
        """Calculate if performance is improving/stable/degrading"""
        if len(perfs) < 3:
            return 'INSUFFICIENT_DATA'
        
        recent = perfs[-3:]
        accuracies = [p.accuracy_rate for p in recent if p.accuracy_rate is not None]
        
        if len(accuracies) < 2:
            return 'INSUFFICIENT_DATA'
        
        if accuracies[-1] > accuracies[0] + 0.05:
            return 'IMPROVING'
        elif accuracies[-1] < accuracies[0] - 0.05:
            return 'DEGRADING'
        else:
            return 'STABLE'
    
    def check_retraining_needed(self, model_name: str, flask_app=None) -> bool:
        """
        Check if a model needs retraining based on verified sample count
        
        Args:
            model_name: Model to check
            flask_app: Flask app for database context
        
        Returns:
            True if retraining should be queued
        """
        app = flask_app or self.app
        if not app:
            return False
        
        with app.app_context():
            # Count unprocessed verifications for this model
            count = db.session.query(VerificationLog).join(
                DetectionLog,
                VerificationLog.detection_log_id == DetectionLog.id
            ).filter(
                DetectionLog.model_name == model_name,
                VerificationLog.processed == False,
                VerificationLog.verification_result.in_(['CORRECT', 'INCORRECT'])
            ).count()
            
            return count >= MIN_VERIFIED_SAMPLES_FOR_RETRAINING
    
    def queue_for_retraining(
        self,
        model_name: str,
        priority: str = 'MEDIUM',
        flask_app=None
    ) -> Optional[int]:
        """
        Queue a model for retraining
        
        Args:
            model_name: Model to retrain
            priority: Priority level (LOW, MEDIUM, HIGH)
            flask_app: Flask app for database context
        
        Returns:
            Training queue ID if successful
        """
        app = flask_app or self.app
        if not app:
            return None
        
        with app.app_context():
            try:
                # Check if already queued
                existing = TrainingQueue.query.filter_by(
                    model_name=model_name,
                    status='PENDING'
                ).first()
                
                if existing:
                    logger.info(f"Model {model_name} already queued for retraining")
                    return existing.id
                
                # Count verified samples
                sample_count = db.session.query(VerificationLog).join(
                    DetectionLog,
                    VerificationLog.detection_log_id == DetectionLog.id
                ).filter(
                    DetectionLog.model_name == model_name,
                    VerificationLog.processed == False,
                    VerificationLog.verification_result.in_(['CORRECT', 'INCORRECT'])
                ).count()
                
                # Create queue entry
                queue_entry = TrainingQueue(
                    model_name=model_name,
                    priority=priority,
                    verified_sample_count=sample_count,
                    status='PENDING'
                )
                
                db.session.add(queue_entry)
                db.session.commit()
                
                logger.info(f"Queued {model_name} for retraining ({sample_count} verified samples)")
                return queue_entry.id
                
            except Exception as e:
                logger.error(f"Error queuing model for retraining: {str(e)}")
                db.session.rollback()
                return None
