"""
CASS - VLM Verification Background Service
Background thread that processes sampled detections for VLM verification
"""
import time
import logging
from threading import Thread
from datetime import datetime

logger = logging.getLogger(__name__)


def _vlm_verification_worker_function(detection_pipeline):
    """
    Background worker that processes VLM verification queue
    
    This function is designed to be added as a method to DetectionPipeline class
    """
    logger.info("VLM Verification worker started")
    
    from config import VLM_BATCH_SIZE
    batch_size = VLM_BATCH_SIZE
    
    while True:
        try:
            if not detection_pipeline.learning_system or not detection_pipeline.vlm_verifier:
                time.sleep(60)
                continue
            
            # Get pending verifications from queue
            pending = detection_pipeline.learning_system.get_verification_queue(limit=batch_size)
            
            if not pending:
                # No work to do, sleep for a minute
                time.sleep(60)
                continue
            
            logger.info(f"Processing {len(pending)} detection verifications...")
            
            # Process each verification
            successful = 0
            for item in pending:
                try:
                    # Call VLM verifier
                    vlm_result = detection_pipeline.vlm_verifier.verify_detection(
                        image_path=item['image_path'],
                        model_name=item['model_name'],
                        detection_data=item['detection_data']
                    )
                    
                    if vlm_result:
                        # Add image path to result
                        vlm_result['image_path'] = item['image_path']
                        
                        # Store verification in database
                        detection_pipeline.learning_system.process_vlm_verification(
                            detection_log_id=item['detection_log_id'],
                            vlm_result=vlm_result,
                            flask_app=detection_pipeline.flask_app
                        )
                        
                        successful += 1
                        logger.info(f"  ✓ Verified detection {item['detection_log_id']}: {vlm_result['verification_result']}")
                    else:
                        logger.warning(f"  ✗ VLM verification failed for detection {item['detection_log_id']}")
                
                except Exception as e:
                    logger.error(f"Error verifying detection {item.get('detection_log_id')}: {str(e)}")
            
            # Remove processed items from queue
            detection_pipeline.learning_system.clear_verification_queue(count=len(pending))
            
            logger.info(f"VLM verification batch complete: {successful}/{len(pending)} successful")
            
            # Check if any models need retraining
            try:
                from config import DETECTION_MODELS
                for model_name in DETECTION_MODELS.keys():
                    if detection_pipeline.learning_system.check_retraining_needed(model_name, detection_pipeline.flask_app):
                        logger.info(f"Model '{model_name}' has enough verified samples for retraining")
                        detection_pipeline.learning_system.queue_for_retraining(
                            model_name=model_name,
                            priority='MEDIUM',
                            flask_app=detection_pipeline.flask_app
                        )
            except Exception as e:
                logger.error(f"Error checking retraining status: {str(e)}")
            
            # Small sleep before next batch
            time.sleep(10)
        
        except Exception as e:
            logger.error(f"Error in VLM verification worker: {str(e)}")
            time.sleep(60)


# Add this function as a method to DetectionPipeline class
# In the actual code, this would be: DetectionPipeline._vlm_verification_worker = _vlm_verification_worker_function
