"""
CEMSS - Analytics Engine
Core analytics computation and data aggregation
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, DetectionLog, Alert, Camera
import json


class AnalyticsEngine:
    """Core analytics engine for detection and alert metrics"""
    
    def __init__(self, db_session=None):
        """Initialize analytics engine"""
        self.db_session = db_session or db.session
    
    def get_detection_timeline(self, start_date=None, end_date=None, camera_id=None, model_name=None):
        """
        Get detection timeline data for visualization
        
        Args:
            start_date: Start datetime (default: 24 hours ago)
            end_date: End datetime (default: now)
            camera_id: Filter by camera ID
            model_name: Filter by model name
        
        Returns:
            dict: Timeline data with hourly aggregation
        """
        # Default to last 24 hours
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(hours=24)
        
        # Build query
        query = self.db_session.query(
            func.strftime('%Y-%m-%d %H:00:00', DetectionLog.timestamp).label('hour'),
            DetectionLog.model_name,
            func.count(DetectionLog.id).label('count')
        ).filter(
            DetectionLog.timestamp >= start_date,
            DetectionLog.timestamp <= end_date
        )
        
        if camera_id:
            query = query.filter(DetectionLog.camera_id == camera_id)
        if model_name:
            query = query.filter(DetectionLog.model_name == model_name)
        
        query = query.group_by('hour', DetectionLog.model_name).order_by('hour')
        results = query.all()
        
        # Format for chart
        timeline = {}
        for row in results:
            hour, model, count = row
            if hour not in timeline:
                timeline[hour] = {}
            timeline[hour][model] = count
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'timeline': timeline
        }
    
    def get_detection_distribution(self, period='24h', camera_id=None):
        """
        Get detection distribution by model and camera
        
        Args:
            period: Time period ('24h', '7d', '30d')
            camera_id: Filter by camera ID
        
        Returns:
            dict: Distribution data
        """
        # Parse period
        hours_map = {'24h': 24, '7d': 168, '30d': 720}
        hours = hours_map.get(period, 24)
        start_date = datetime.now() - timedelta(hours=hours)
        
        # Query by model
        query_model = self.db_session.query(
            DetectionLog.model_name,
            func.count(DetectionLog.id).label('count')
        ).filter(
            DetectionLog.timestamp >= start_date
        )
        
        if camera_id:
            query_model = query_model.filter(DetectionLog.camera_id == camera_id)
        
        model_dist = query_model.group_by(DetectionLog.model_name).all()
        
        # Query by camera
        query_camera = self.db_session.query(
            Camera.name,
            func.count(DetectionLog.id).label('count')
        ).join(
            DetectionLog, Camera.id == DetectionLog.camera_id
        ).filter(
            DetectionLog.timestamp >= start_date
        )
        
        if camera_id:
            query_camera = query_camera.filter(Camera.id == camera_id)
        
        camera_dist = query_camera.group_by(Camera.name).all()
        
        # Query by severity
        query_severity = self.db_session.query(
            DetectionLog.severity_level,
            func.count(DetectionLog.id).label('count')
        ).filter(
            DetectionLog.timestamp >= start_date,
            DetectionLog.severity_level.isnot(None)
        )
        
        if camera_id:
            query_severity = query_severity.filter(DetectionLog.camera_id == camera_id)
        
        severity_dist = query_severity.group_by(DetectionLog.severity_level).all()
        
        return {
            'period': period,
            'by_model': {model: count for model, count in model_dist},
            'by_camera': {camera: count for camera, count in camera_dist},
            'by_severity': {level: count for level, count in severity_dist if level}
        }
    
    def get_camera_health_metrics(self, camera_id=None):
        """
        Get camera health and activity metrics
        
        Args:
            camera_id: Specific camera ID or None for all
        
        Returns:
            dict or list: Health metrics
        """
        cameras = Camera.query.filter_by(is_active=True).all() if not camera_id else [Camera.query.get(camera_id)]
        
        metrics = []
        for camera in cameras:
            if not camera:
                continue
            
            # Get detection count (last 24h)
            recent_detections = DetectionLog.query.filter(
                DetectionLog.camera_id == camera.id,
                DetectionLog.timestamp >= datetime.now() - timedelta(hours=24)
            ).count()
            
            # Get last detection time
            last_detection = DetectionLog.query.filter_by(
                camera_id=camera.id
            ).order_by(DetectionLog.timestamp.desc()).first()
            
            # Get alert count (last 24h)
            recent_alerts = Alert.query.filter(
                Alert.camera_id == camera.id,
                Alert.sent_at >= datetime.now() - timedelta(hours=24)
            ).count()
            
            metrics.append({
                'camera_id': camera.id,
                'camera_name': camera.name,
                'is_active': camera.is_active,
                'detection_enabled': camera.detection_enabled,
                'detections_24h': recent_detections,
                'alerts_24h': recent_alerts,
                'last_detection': last_detection.timestamp.isoformat() if last_detection else None,
                'active_models': camera.get_active_models()
            })
        
        return metrics[0] if camera_id and metrics else metrics
    
    def get_summary_stats(self, period='24h'):
        """
        Get overall summary statistics
        
        Args:
            period: Time period
        
        Returns:
            dict: Summary stats
        """
        hours_map = {'24h': 24, '7d': 168, '30d': 720}
        hours = hours_map.get(period, 24)
        start_date = datetime.now() - timedelta(hours=hours)
        
        total_detections = DetectionLog.query.filter(
            DetectionLog.timestamp >= start_date
        ).count()
        
        total_alerts = Alert.query.filter(
            Alert.sent_at >= start_date
        ).count()
        
        high_severity = DetectionLog.query.filter(
            DetectionLog.timestamp >= start_date,
            DetectionLog.severity_level.in_(['HIGH', 'CRITICAL'])
        ).count()
        
        active_cameras = Camera.query.filter_by(is_active=True).count()
        
        # Most active camera
        most_active = self.db_session.query(
            Camera.name,
            func.count(DetectionLog.id).label('count')
        ).join(
            DetectionLog, Camera.id == DetectionLog.camera_id
        ).filter(
            DetectionLog.timestamp >= start_date
        ).group_by(Camera.name).order_by(func.count(DetectionLog.id).desc()).first()
        
        return {
            'period': period,
            'total_detections': total_detections,
            'total_alerts': total_alerts,
            'high_severity_count': high_severity,
            'active_cameras': active_cameras,
            'most_active_camera': most_active[0] if most_active else None,
            'most_active_detections': most_active[1] if most_active else 0
        }
