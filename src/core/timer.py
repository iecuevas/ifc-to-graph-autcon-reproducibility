import time 
import logging

from functools import wraps


def stopwatch(func: callable) -> callable:
    """
    Decorador para medir el tiempo de ejecución de una función.
    Args:
        func (callable): Función a medir.
    Returns:
        callable: Función decorada.
    """
    @wraps(func)
    def timed(*args, **kwargs):
        self = args[0] if args and hasattr(args[0], "_logger") else None
        logger = self._logger if self else logging.getLogger(func.__module__)
        logger.info(f"Function '{func.__name__}' started")
        
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        time_taken = end - start
        
        logger.info(f"{func.__name__} was executed in: {time_taken:.6f} seconds")
        return result
    return timed
