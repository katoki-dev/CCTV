"""
CEMSS - Detection Configuration Module
Centralized detection quality and smoothing settings
"""
from config import (
    TEMPORAL_SMOOTHING_ENABLED,
    TEMPORAL_SMOOTHING_FRAMES,
    MIN_CONFIDENCE_OVERRIDES,
    MULTI_MODEL_FUSION_ENABLED,
    FUSION_BOOST_FACTOR,
    FUSION_COMBINATIONS
)


class DetectionConfig:
    """Centralized detection configuration"""
    
    # Temporal smoothing settings
    TEMPORAL_SMOOTHING_ENABLED = TEMPORAL_SMOOTHING_ENABLED
    TEMPORAL_SMOOTHING_FRAMES = TEMPORAL_SMOOTHING_FRAMES
    
    # Confidence thresholds
    MIN_CONFIDENCE = MIN_CONFIDENCE_OVERRIDES
    
    # Multi-model fusion
    FUSION_ENABLED = MULTI_MODEL_FUSION_ENABLED
    FUSION_BOOST = FUSION_BOOST_FACTOR
    FUSION_RULES = FUSION_COMBINATIONS
    
    @staticmethod
    def get_required_frames(model_name):
        """Get number of required consecutive frames for a model"""
        if not DetectionConfig.TEMPORAL_SMOOTHING_ENABLED:
            return 1
        return DetectionConfig.TEMPORAL_SMOOTHING_FRAMES.get(model_name, 2)
    
    @staticmethod
    def get_min_confidence(model_name):
        """Get minimum confidence threshold for a model"""
        return DetectionConfig.MIN_CONFIDENCE.get(model_name, 0.5)
    
    @staticmethod
    def get_fusion_boost(models):
        """
        Get confidence boost for correlated multi-model detections
        
        Args:
            models: List of concurrent model names (e.g., ['person', 'phone'])
        
        Returns:
            float: Confidence boost factor
        """
        if not DetectionConfig.FUSION_ENABLED or len(models) < 2:
            return 0.0
        
        # Sort models to create consistent key
        model_key = '+'.join(sorted(models))
        
        # Check for specific fusion rule
        fusion_rule = DetectionConfig.FUSION_RULES.get(model_key)
        if fusion_rule:
            return fusion_rule.get('boost', DetectionConfig.FUSION_BOOST)
        
        # Default fusion boost
        return DetectionConfig.FUSION_BOOST
    
    @staticmethod
    def get_fusion_severity_modifier(models):
        """Get severity modifier for correlated detections"""
        if not DetectionConfig.FUSION_ENABLED or len(models) < 2:
            return 0
        
        model_key = '+'.join(sorted(models))
        fusion_rule = DetectionConfig.FUSION_RULES.get(model_key)
        if fusion_rule:
            return fusion_rule.get('severity_modifier', 0)
        
        return 0
