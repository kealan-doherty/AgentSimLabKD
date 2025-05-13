from typing import List, Tuple
import re # Parse model response to decide if we should end the conversation.
          # TODO: replace this with a tool call?
from datetime import datetime
from model import GeminiModel, Prompt, RateLimitTracker
import yaml 

## Basic Memory Class (modified, simplified more)
class SimpleMemory:
  def __init__(self, memories: List[str] = None)  -> None:
    if memories is None:
      memories = []
    self._store: List[str] = memories

  ## Do this if a SimpleMemory object is converted to a string
  ##  or used in a string context
  def __str__(self):
    if len(self._store) == 0 :
      return "N/A"
    return yaml.dump(self.retrieve_recent_memories(-1),sort_keys=False)

  def add_memory(self, text: str) -> None:
    self._store.append(text)

  def retrieve_recent_memories(self, n) -> str:
    """
    Returns the most recent n memories.

    Returns all memories if n < 0
    """
    if n < 0:
      return self._store
    elif len(self._store) < n:
      return self._store
    else:
      return self._store[-n:]

class Location:
  pass

## Basic Agent Class (first draft by o3, then refactored)
class SimpleAgent:
  def __init__(self,
               name:str ,
               **kwargs,
               ) -> None:
    """
    Args: 
    - name (str): required, must be unique
    - list of all other attributes
      - required: model (GeminiModel), tools (List)
      - optional: any other attribute you'd like the model to store
                  (eg persona, memory, location, etc.)
      - IMPORTANT: each `optional` object MUST have a __str__ function defined for its object
    """
    self.name = name
  
    special_attribute_keys = ["model","tools"]
    # When subclassing, expand to other types of 'specially handled' variables
    # special_attribute_keys = ["model","tools","location","memory"]
    self.model = kwargs["model"] if "model" in kwargs else GeminiModel()
    self.tools = kwargs["tools"] if "tools" in kwargs else []

    if "attribute_dictionary" in kwargs:
     self.attribute_dictionary = kwargs["attribute_dictionary"]
    else:
      self.attribute_dictionary ={}

    for key,val in kwargs.items():
      if key not in special_attribute_keys:
        self.attribute_dictionary[key] = val

  def __str__(self):
    return self.description()
  
  def add_memory(self, memory_string):
    if "memory" in self.attribute_dictionary:
      self.attribute_dictionary["memory"].add_memory( memory_string )
      return 
    else:
      raise ValueError(f"Error: {self.name} has no memory object to store {memory_string}")

  def generate_content(self,**kwargs):
    """
    Generate content using a prompt made up of 
        1. Internal attributes, and 
        2. Passed arguments
    Prompt string will be genrated using yaml.dump

    Arguments: 
      - A dictionary of any/all fields you want to appear in the prompt
        (dictionary will be converted to YAML output)
    Notes
      - (optional) "model_parameters" (dict) = dictionary of model objects you want passed to the LLM call
      - (behavior) Override internal attributes by providing option with same key in kwargs

    IMPORTANT:
      - (all objects stored in attribute_dictionary MUST have a __str__ method).
    """
    # model_params = kwargs["model_parameters"] if "model_parameters" in kwargs else {}
    special_args = ["model_parameters"]
    if "model_parameters" in kwargs:
      model_params = kwargs["model_parameters"] 
    elif "tools" in kwargs:
      model_params = {"tools":kwargs["tools"]}
    else:
      model_params = {}

    arg_dict = {key:str(val) for key,val in kwargs.items() if key not in special_args }
    attribute_dict = {key:str(val) for key,val in self.attribute_dictionary.items()}
    # Generate prompt from union of agent attributes and  kwargs
    #  Kwargs comes second, so overrides agent attributes if conflict
    prompt_dictionary = attribute_dict | arg_dict 
    prompt = Prompt(**prompt_dictionary)
    prompt = prompt.generate()
    # print(prompt)
    # print(model_params)
    response = self.model.generate_content(user_prompt=prompt, **model_params)
    return response


  def generate_plan(self,**kwargs):    
    prompt_dict = kwargs
    prompt_dict["name"] = self.name
    prompt_dict["description"] = self.description() 
    
    prompt_dict["instruction"] = f"First, identify what would {self.name} do.  Then make a very short plan to achieve those goals.  Find a SMALL NUMBER of concrete steps that can be taken.  Take available tools into account in your planning, but DO NOT do any tool calls."
    
    if "location" in self.attribute_dictionary:
      # prompt_dict["location description"] = self.attribute_dictionary["location"].description()
      prompt_dict["current location"] = self.attribute_dictionary["location"].name

    response = self.generate_content(**prompt_dict)    

    return response.text


  def generate_action(self,**kwargs):
    """
    Sets *ACTION* instruction, then calls generate_content, passing all kwargs
    """
    prompt_dict = kwargs
    prompt_dict["name"] = self.name
    prompt_dict["description"] = self.description() 
    
    # prompt_dict["instruction"] = f"What would {self.name} do? "\
    #                               "State the action and describe its results."
    prompt_dict["instruction"] = f"What would {self.name} do? "
    
    if "system" not in kwargs and "tools" in kwargs: 
      prompt_dict["system"] = f"You are {self.model.model_name}, a tool using model from Google. Use tools when needed."

    if "location" in self.attribute_dictionary:
      prompt_dict["location description"] = self.attribute_dictionary["location"].description()

    response = self.generate_content(**prompt_dict)    

    return response

  def generate_speech(self, **kwargs):
    """
    Sets *SPEECH* instruction, then calls generate_content, passing all kwargs
    """
    prompt_dict = kwargs
    prompt_dict["name"] = self.name
    prompt_dict["description"] = self.description() 

    if "interlocutor_name" in kwargs:
      prompt_dict["instruction"] = f"What would {self.name} say to {kwargs["interlocutor_name"]}?"
    else:
      prompt_dict["instruction"] = f"What would {self.name} say?"

    if "location" in self.attribute_dictionary:
      prompt_dict["location description"] = self.attribute_dictionary["location"].description()

    response = self.generate_content(**prompt_dict)    
    return response.text

  def description_dictionary(self):
    """Returns dictionary that can be printed with yaml.dump"""
    description = {
      "Agent Name": self.name,
    }
    str_attribute_dict = {key:str(val) for key,val in self.attribute_dictionary.items()}
    description = description | str_attribute_dict
    # if "location" is not None:
    #   description["Location"] = self.location.name
    return description

  def description(self):
    return yaml.dump(self.description_dictionary())

  def get_location(self):
    return self.attribute_dictionary["location"] if "location" in self.attribute_dictionary else None

  def set_location(self, location):
    self.attribute_dictionary["location"] = location

  def get_persona(self):
    return self.attribute_dictionary["persona"] if "persona" in self.attribute_dictionary else None

  def set_persona(self, persona):
    self.attribute_dictionary["persona"] = persona
