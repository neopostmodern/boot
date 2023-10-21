import json
import traceback
from inspect import signature
from subprocess import run
from flask import Flask, request, send_from_directory
from client.hardware import Hardware
import client.constants as constants

ServoName = constants.ServoName
h = Hardware()

app = Flask(__name__, static_url_path='/static')

# Serve the index.html file from the 'static' directory
@app.route('/')
def serve_index():
  return send_from_directory('static', 'index.html')

@app.route('/introspection')
def introspection():
  system = {}
  
  for path in dir(h):
    if path.startswith('_'):
      continue
    
    prop = getattr(h, path)
    system[path] = {}
    for nested_path in dir(prop):
      if nested_path.startswith('_'):
        continue

      nested_prop = getattr(prop, nested_path)
      if not callable(nested_prop):
        continue
        
      documentation_hints = []
      if nested_prop.__doc__ is not None:
        for hint in nested_prop.__doc__.split(','):
          if hint.startswith('servo:'):
            servo_name = constants.ServoName(hint.split(':')[1])
            servo_config = constants.ServoConfigs[servo_name]
            documentation_hints.append({
              "type": "servo",
              "min_angle": servo_config.min_angle,
              "max_angle": servo_config.max_angle,
            })
          else:
            print(f"Unknown hint '{hint}' for {path}.{nested_path}")
    
      arguments = []
      sig = signature(nested_prop)
      for parameter_name in sig.parameters:
        if parameter_name == 'args' or parameter_name == 'kwargs':
          continue
        argument_type = sig.parameters[parameter_name].annotation.__name__
        arguments.append({ 'name': parameter_name, 'type': None if argument_type == '_empty' else argument_type })
        
      system[path][nested_path] = {"arguments": arguments, "hints": documentation_hints}
    
  return system
  
@app.route('/constants')
def constants_():
  constants_summary = {}
  for constant_name in dir(constants):
    if constant_name.startswith('_') or constant_name in ['Enum', 'NamedTuple', 'Union', 'ServoConfig']:
      continue
    
    constant = getattr(constants, constant_name)
    if type(constant) in [str, int]:
      constants_summary[constant_name] = constant
    elif type(constant) == dict:
      pass
      # too hard for now
    elif type(constant).__name__ == 'EnumMeta':
      constants_summary[constant_name] = {}
      for entry in constant:
        constants_summary[constant_name][entry.name] = entry.value
    elif type(constant) == type:
      constants_summary[constant_name] = {}
      for property_name in dir(constant):
        if property_name.startswith('_'):
          continue
          
        constants_summary[constant_name][property_name] = getattr(constant, property_name)
      
    else:
      print(constant_name, type(constant), constant)

  return constants_summary

@app.route('/exec')
def exec():
  method = request.args.get('method')
  
  if method == 'sudo reboot now':
    run("sudo reboot now", shell=True)
    return
  
  parameters = ''
  for parameter_name in request.args:
    if parameter_name == 'method':
      continue
    
    parameter_value = request.args.get(parameter_name)
    if parameter_value == '':
      continue
    
    parameters += f"{parameter_name}={parameter_value}, "
    
  command = f"h.{method}({parameters})"
  log = [f"> {command}"]
  try:
    result = eval(command)
    if result is None:
      log.append("< None")
    else:
      log.append(f"< {result}")
  except Exception as error:
    log.append(f"! {error.__class__.__name__}: {str(error)}")
    print(error)
    print(traceback.format_exc())
  
  return '\n'.join(log)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)


