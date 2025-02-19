import subprocess
import sys
import json
import time
import requests
import psutil
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalTestRunner:
    """Runs comprehensive final tests before release."""
    
    def __init__(self):
        self.results = {
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'overall_status': 'pending'
        }
        self.test_dir = Path('test_results')
        self.test_dir.mkdir(exist_ok=True)
    
    def run_all_tests(self):
        """Run all final tests."""
        tests = [
            self.run_unit_tests,
            self.run_system_tests,
            self.run_integration_tests,
            self.run_performance_tests,
            self.run_security_tests,
            self.check_documentation
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self._record_test(test.__name__, 'failed', str(e))
                logger.error(f"Test {test.__name__} failed: {e}")
        
        self._save_results()
        return self.results
    
    def run_unit_tests(self):
        """Run all unit tests with coverage."""
        logger.info("Running unit tests...")
        result = subprocess.run(
            ['pytest', 'tests/unit', '--cov=src', '--cov-report=html'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self._record_test('unit_tests', 'failed', result.stderr)
            raise Exception("Unit tests failed")
            
        self._record_test('unit_tests', 'passed')
    
    def run_system_tests(self):
        """Run system integration tests."""
        logger.info("Running system tests...")
        result = subprocess.run(
            ['pytest', 'tests/system', '-v'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self._record_test('system_tests', 'failed', result.stderr)
            raise Exception("System tests failed")
            
        self._record_test('system_tests', 'passed')
    
    def run_integration_tests(self):
        """Run integration tests with external components."""
        logger.info("Running integration tests...")
        
        # Start required services
        services = self._start_services()
        
        try:
            # Test API endpoints
            self._test_api_endpoints()
            
            # Test database operations
            self._test_database()
            
            # Test model serving
            self._test_model_serving()
            
            self._record_test('integration_tests', 'passed')
            
        finally:
            # Cleanup
            self._stop_services(services)
    
    def run_performance_tests(self):
        """Run performance and load tests."""
        logger.info("Running performance tests...")
        
        # Start services
        services = self._start_services()
        
        try:
            # Test latency
            latency = self._measure_latency()
            
            # Test throughput
            throughput = self._measure_throughput()
            
            # Test resource usage
            resource_usage = self._measure_resource_usage()
            
            results = {
                'latency': latency,
                'throughput': throughput,
                'resource_usage': resource_usage
            }
            
            # Check against thresholds
            if (latency > 100 or throughput < 50 or 
                resource_usage['cpu'] > 80 or 
                resource_usage['memory'] > 1024):
                self._record_test('performance_tests', 'failed', str(results))
                raise Exception("Performance tests failed")
                
            self._record_test('performance_tests', 'passed', str(results))
            
        finally:
            self._stop_services(services)
    
    def run_security_tests(self):
        """Run security checks."""
        logger.info("Running security tests...")
        
        checks = [
            ('Checking dependencies...', ['safety', 'check']),
            ('Running bandit scan...', ['bandit', '-r', 'src']),
            ('Checking secrets...', ['detect-secrets', 'scan', './'])
        ]
        
        for message, command in checks:
            logger.info(message)
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                self._record_test('security_tests', 'failed', result.stderr)
                raise Exception(f"Security check failed: {' '.join(command)}")
        
        self._record_test('security_tests', 'passed')
    
    def check_documentation(self):
        """Verify documentation completeness."""
        logger.info("Checking documentation...")
        
        required_docs = [
            'docs/user_guide.md',
            'docs/deployment_guide.md',
            'docs/monitoring_guide.md',
            'docs/release_notes.md'
        ]
        
        missing_docs = [doc for doc in required_docs if not Path(doc).exists()]
        
        if missing_docs:
            self._record_test('documentation_check', 'failed', 
                            f"Missing docs: {missing_docs}")
            raise Exception("Documentation incomplete")
            
        self._record_test('documentation_check', 'passed')
    
    def _record_test(self, name, status, details=None):
        """Record test results."""
        self.results['tests'].append({
            'name': name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details
        })
    
    def _save_results(self):
        """Save test results to file."""
        self.results['end_time'] = datetime.now().isoformat()
        self.results['overall_status'] = (
            'passed' if all(t['status'] == 'passed' for t in self.results['tests'])
            else 'failed'
        )
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = self.test_dir / f'final_test_results_{timestamp}.json'
        
        with open(result_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"Test results saved to {result_file}")
    
    def _start_services(self):
        """Start required services for testing."""
        services = []
        
        # Start API server
        api_server = subprocess.Popen(
            ['uvicorn', 'src.api.routes:router', '--port', '8001'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        services.append(('api_server', api_server))
        
        # Wait for services to start
        time.sleep(2)
        
        return services
    
    def _stop_services(self, services):
        """Stop running services."""
        for name, process in services:
            process.terminate()
            process.wait()

def main():
    """Run final tests."""
    runner = FinalTestRunner()
    results = runner.run_all_tests()
    
    if results['overall_status'] == 'passed':
        logger.info("All final tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("Final tests failed. Check results for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 