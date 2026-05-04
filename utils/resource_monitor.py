"""
CASS - Resource Monitor
Monitor system resources (CPU, memory, GPU, disk)
"""
import psutil
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import torch
    GPU_AVAILABLE = torch.cuda.is_available()
except ImportError:
    GPU_AVAILABLE = False
    logger.info("PyTorch not available, GPU monitoring disabled")


class ResourceMonitor:
    """Monitor system resource usage"""
    
    def __init__(self, memory_threshold_percent=90, disk_threshold_percent=90):
        """
        Initialize resource monitor
        
        Args:
            memory_threshold_percent: Alert when memory usage exceeds this %
            disk_threshold_percent: Alert when disk usage exceeds this %
        """
        self.memory_threshold = memory_threshold_percent
        self.disk_threshold = disk_threshold_percent
        
    def get_cpu_usage(self):
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)
    
    def get_memory_info(self):
        """
        Get memory usage information
        
        Returns:
            dict: Memory statistics
        """
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3),
            'used_gb': mem.used / (1024**3),
            'percent': mem.percent,
            'threshold_exceeded': mem.percent > self.memory_threshold
        }
    
    def get_gpu_info(self):
        """
        Get GPU usage information (if available)
        
        Returns:
            dict: GPU statistics or None if not available
        """
        if not GPU_AVAILABLE:
            return None
        
        try:
            gpu_info = {
                'available': True,
                'device_count': torch.cuda.device_count(),
                'devices': []
            }
            
            for i in range(torch.cuda.device_count()):
                device_props = torch.cuda.get_device_properties(i)
                mem_allocated = torch.cuda.memory_allocated(i) / (1024**3)
                mem_reserved = torch.cuda.memory_reserved(i) / (1024**3)
                mem_total = device_props.total_memory / (1024**3)
                
                gpu_info['devices'].append({
                    'id': i,
                    'name': torch.cuda.get_device_name(i),
                    'memory_allocated_gb': mem_allocated,
                    'memory_reserved_gb': mem_reserved,
                    'memory_total_gb': mem_total,
                    'memory_percent': (mem_allocated / mem_total) * 100 if mem_total > 0 else 0
                })
            
            return gpu_info
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
            return None
    
    def get_disk_usage(self, path='/'):
        """
        Get disk usage for a specific path
        
        Args:
            path: Path to check disk usage
        
        Returns:
            dict: Disk usage statistics
        """
        try:
            disk = psutil.disk_usage(path)
            return {
                'path': path,
                'total_gb': disk.total / (1024**3),
                'used_gb': disk.used / (1024**3),
                'free_gb': disk.free / (1024**3),
                'percent': disk.percent,
                'threshold_exceeded': disk.percent > self.disk_threshold
            }
        except Exception as e:
            logger.error(f"Error getting disk usage for {path}: {e}")
            return None
    
    def get_process_info(self):
        """
        Get current process resource usage
        
        Returns:
            dict: Process statistics
        """
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            
            return {
                'pid': process.pid,
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_rss_mb': mem_info.rss / (1024**2),
                'memory_vms_mb': mem_info.vms / (1024**2),
                'num_threads': process.num_threads(),
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None,
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting process info: {e}")
            return None
    
    def get_system_status(self, video_dir=None):
        """
        Get comprehensive system status
        
        Args:
            video_dir: Path to video directory for disk usage check
        
        Returns:
            dict: Complete system status
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': self.get_cpu_usage(),
            'memory': self.get_memory_info(),
            'process': self.get_process_info(),
            'alerts': []
        }
        
        # Add GPU info if available
        gpu_info = self.get_gpu_info()
        if gpu_info:
            status['gpu'] = gpu_info
        
        # Add disk usage
        if video_dir:
            disk_info = self.get_disk_usage(video_dir)
            if disk_info:
                status['disk'] = disk_info
                if disk_info['threshold_exceeded']:
                    status['alerts'].append({
                        'type': 'disk',
                        'severity': 'warning',
                        'message': f"Disk usage at {disk_info['path']} exceeded {self.disk_threshold}%"
                    })
        
        # Check memory threshold
        if status['memory']['threshold_exceeded']:
            status['alerts'].append({
                'type': 'memory',
                'severity': 'warning',
                'message': f"Memory usage exceeded {self.memory_threshold}%"
            })
        
        return status
    
    def check_health(self):
        """
        Check if system is healthy
        
        Returns:
            tuple: (is_healthy, issues_list)
        """
        issues = []
        
        # Check memory
        mem = self.get_memory_info()
        if mem['threshold_exceeded']:
            issues.append(f"High memory usage: {mem['percent']:.1f}%")
        
        # Check CPU
        cpu = self.get_cpu_usage()
        if cpu > 90:
            issues.append(f"High CPU usage: {cpu:.1f}%")
        
        return len(issues) == 0, issues


# Global resource monitor instance
_monitor_instance = None


def get_resource_monitor():
    """Get or create global resource monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ResourceMonitor()
    return _monitor_instance
