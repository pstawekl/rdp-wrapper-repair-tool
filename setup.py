from setuptools import find_packages, setup

setup(
    name="rdp_monitor_service",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'pywin32>=306',
        'requests>=2.31.0',
        'beautifulsoup4>=4.12.2',
        'wmi>=1.5.1',
        'tqdm>=4.65.0',
    ],
    entry_points={
        'console_scripts': [
            'rdp_monitor_service=src.main:main',
            'rdp_monitor_service_install=src.service.windows_service:main',
        ],
    },
    author="Your Name",
    description="Windows service for monitoring RDP version changes",
)
