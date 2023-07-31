import logging

# Create the global logger object
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def initLogger(options, defaultOptions):
    # Logger transports
    logfile = None
    logterm = None

    # Create log console handler
    logterm = logging.StreamHandler()
    logterm.setLevel(logging.INFO)
    logterm.setFormatter(logging.Formatter('%(message)s'))
    
    getLogger().addHandler(logterm)

    # Use default log file name?
    if options['logfile'] is None:
        options['logfile'] = defaultOptions['logfile']

    # Create log file handler
    logfile = logging.FileHandler(options['logfile'])
    logfile.setLevel(logging.DEBUG)

    logger.addHandler(logfile)

    # Set the logging level
    if not options.get('quiet'):
        set_level(logging.INFO)


def getLogger():
    return logger


def set_level(level):
    getLogger().setLevel(level)
