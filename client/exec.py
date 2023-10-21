import functools
from threading import Thread 
from config.config import config
from .constants import Config

def threadable(function):
  @functools.wraps(function)
  def thread_wrapper(*args, **kwargs):
    if config['client'][Config.THREADING]:
      Thread(target=function, args=args, kwargs=kwargs, daemon=True).start()
    else:
      function(*args, **kwargs)
      
  return thread_wrapper
