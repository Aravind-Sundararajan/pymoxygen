import logging

# Create the global logger object
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def init(options, defaultOptions):
    # Logger transports
    logfile = None
    logterm = None

    # Create log console handler
    logterm = logging.StreamHandler()
    logterm.setLevel(logging.WARN)
    logterm.setFormatter(logging.Formatter('%(message)s'))

    logger.addHandler(logterm)

    # User defined log file?
    if 'logfile' in options:
        # Use default log file name?
        if options['logfile'] is True:
            options['logfile'] = defaultOptions['logfile']

        # Create log file handler
        logfile = logging.FileHandler(options['logfile'])
        logfile.setLevel(logging.DEBUG)

        logger.addHandler(logfile)

    # Set the logging level
    if not options.get('quiet'):
        set_level('verbose')

def getLogger():
    return logger

def set_level(level):
    logger.setLevel(level.upper())
