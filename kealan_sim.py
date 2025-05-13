from agent import GeminiModel
from world import World
import datetime
import random
from agent import SimpleAgent



model = GeminiModel("gemini-2.0-flash", 15, 1000)


rooms   = ["living", "kitchen", "bathroom", "bedroom", "office", "garden","gameroom", "closet"]
edges   = [("living","kitchen"), ("living","bathroom"), ("living","bedroom"),
           ("living","office"), ("living","garden"), ("kitchen","garden"), ("kitchen", "closet"),
           ("kitchen", "gameroom"), ("living", "closet"), ("living", "gameroom")]


agents  = [
     {"name":"Susan",
         "observation" : "I need to get some food.",
         "status":"relaxing",
         "persona":"hungry" ,
         "location":"kitchen has food"},
    {"name":"sarah"  ,
         "observation" : "I am in the same room as Kealan we should play rock paper scissors.",
         "status": "speaking",
         "persona":"speaking to kealan about play rock paper scissors. ",
         "location":"gameroom"},
    {"name":"Kealan",
         "observation":" I'm looking for something to do in the gameroom and I will NOT leave the gameroom. ",
         "status":"relaxing",
         "persona":"happy",
         "location":"gameroom"},
    {"name":"Catherine",
        "goal":"I need to go take care of the flowers",
        "status":"driven",
        "persona":"focused ",
        "location":"office"},
]

world = World(location_names=rooms, room_edges=edges,
              agent_descriptions=agents, model=model)


def get_room_description(**kwargs) ->str:
    try:
        room_desc = kwargs["agent"].get_location().description()
        print(f"{kwargs["agent"].name} looks around and sees {room_desc}.")
        return kwargs["agent"].get_location().description()
    except:
        err_msg = f"Error: missing argument for get_room_description in {kwargs}"
        print(err_msg)
        return err_msg
describe_tool = model.register_tool(
    func        = get_room_description,          # pure function from tools.py
    description = "Look around the current room",
    parameters  = {})

def move(**kwargs) -> str:
    try:
        result = kwargs["world"].move(agent=kwargs["agent"], dest_name=kwargs["destination"] )

        # TODO: Handle invalid arguments (e.g. inaccessible destination?)
        return result
    except:
        err_msg = f"Error: missing argument for move_tool in {kwargs}"
        print(err_msg)
        return err_msg
move_tool = model.register_tool(
    func        = move,             # pure function from tools.py
    description = "Move to an adjacent room",
    parameters  = {
        "destination": {
            "type": "string",
            "description": "The name of the room to move to."
        }
    })
def speak(**kwargs) -> str:
    try:
        return kwargs["agent"].generate_speech(interlocutor_name=kwargs["interlocutor_name"])
    except:
        print("ERROR SPEAKING")
        return "ERROR SPEAKING"
speak_tool = model.register_tool(
    func = speak,
    description="Talk to a named individual",
    parameters={
        "interlocutor_name" :{
            "type" : "string",
            "description" : "The name of the individual you are talking to."
        }
    }
)

def drink_coffee(**kwargs) ->str:
    energy_levels = ["exhausted", "tried", "normal", "energetic"]
    agent_energy_levels = kwargs["agent"].get_persona()

    if agent_energy_levels == energy_levels[0]:
        print(f"{kwargs["agent"].name} is exhausted so drinks a espresso to be energetic.")
        return kwargs["agent"].set_persona("energetic")
    elif agent_energy_levels == energy_levels[1]:
        print(f"{kwargs["agent"].name} is tired so drinks a americano to be normal.")
        return kwargs["agent"].set_persona("normal")
    elif agent_energy_levels == energy_levels[2]:
        print(f"{kwargs["agent"].name} is normal so drinks a coffee to be energetic.")
        return kwargs["agent"].set_persona("energetic")
    elif agent_energy_levels == energy_levels[3]:
        print(f"{kwargs["agent"].name} is energetic so doesn't drink any coffee because they don't need it.")
        return kwargs["agent"].set_persona("energetic")
    else:
        print(f"ERROR no energy level detected for {kwargs["agent"].name} so they can't have any coffee")
        return f"ERROR no energy level detected for {kwargs["agent"].name} so they can't have any coffee"
drink_coffee_tool = model.register_tool(
    func = drink_coffee,
    description="To drink a coffee based on agents persona",
    parameters={
        }
)



def eat_food(**kwargs) ->str:
    today = datetime.date.today()
    day_of_week_int = today.weekday()
    agent_hunger = kwargs["agent"].get_persona()
    if agent_hunger != "hungry":
        return f"{kwargs["agent"].name} doesn't eat because they arent hungry"
    elif day_of_week_int == 0:
        print(f"{kwargs["agent"].name} eats a salad because it is Meatless Monday")
        return kwargs["agent"].set_persona("satisfied")
    elif day_of_week_int == 1:
        print(f"{kwargs["agent"].name} eats a taco because it is Taco Tuesday")
        return kwargs["agent"].set_persona("satisfied")
    elif day_of_week_int == 2:
        print( f"{kwargs["agent"].name} eats a Waffle because it is Waffle Wednesday")
        return kwargs["agent"].set_persona("satisfied")
    elif day_of_week_int == 3:
        print(f"{kwargs["agent"].name} eats a pizza because it is Throwback Thrusday")
        return kwargs["agent"].set_persona("satisfied")
    elif day_of_week_int == 4:
        print(f"{kwargs["agent"].name} eats fish and chips because it is Fish Fry Friday")
        return kwargs["agent"].set_persona("satisfied")
    elif day_of_week_int == 5:
        print(f"{kwargs["agents"].name} eats a bowl of soup because it is Soup-er Saturday")
        return kwargs["agent"].set_persona("satisfied")
    elif day_of_week_int == 6:
        print(f"{kwargs["agent"].name} eats a pot roast because it is Slow Cooker Sunday")
        return kwargs["agent"].set_persona("satisfied")
eat_food_tool = model.register_tool(
    func = eat_food,
    description="eat food based on the agent's persona and the day of the week",
    parameters={}
)


def play_rock_paper_scissors(target_name: str, **kwargs) ->str:
    agent1_play = ''
    agent2_play =''

    agent1 = kwargs["agent"] # sarah if sarah calls the function
    # get agent2 from world based on ghe NAME
    myworld = kwargs["world"]
    agent2 = myworld.get_agent(target_name)


    agent1_play = random.choice(["rock", "paper", "scissors"])
    agent2_play = random.choice(["rock", "paper", "scissors"])

    if agent1_play == agent2_play:
        return f"{agent1.name} and {agent2.name} had {agent1_play} so it's a tie and no winner"

    elif agent1_play == "rock" and agent2_play == "paper":
        print(f"{agent1.name} has paper and {agent2.name }has rock {agent2.name} wins")
        return agent1.set_persona("happy") and agent2.set_persona("mad")
    elif agent1_play == "rock" and agent2_play == "scissors":
        print (f"{agent2.name} has scissors and {agent1.name}had rock {agent1.name} wins")
        return agent1.set_persona("happy") and agent2.set_persona("mad")

    elif agent1_play == "paper" and agent2_play == "scissors":
        print(f"{agent2.name} has scissors and {agent1.name} has paper {agent2.name} wins")
        return agent1.set_persona("mad") and  agent2.set_persona("happy")
    elif agent1_play == "paper" and agent2_play == "rock":
        print (f"{agent1.name} has paper and {agent2.name} has rock {agent1.name} wins")
        return  agent1.set_persona("happy") and agent2.set_persona("mad")

    elif agent1_play == "scissors" and agent2_play == "paper":
        print(f" {agent1.name} has scissors and {agent2.name} has paper {agent1.name} wins")
        return agent1.set_persona("happy") and agent2.set_persona("mad")
    elif agent1_play == "scissors" and agent2_play == "rock":
        print(f"{agent1.name} has scissors and {agent2.name} has rock {agent2.name} wins")
        return agent1.set_persona("mad") and agent2.set_persona("happy")

play_rock_paper_scissors = model.register_tool(
    func = play_rock_paper_scissors,
    description="a game of rock paper scissors",
    parameters={
        "target_name":{ "type": "string",
            "description": "name of person you want to play rock paper scissors with"


    }}
)


TOOLS = [move_tool, describe_tool, drink_coffee_tool,eat_food_tool, play_rock_paper_scissors]

# ---------- 4.  Tiny Simulation with step() ---------------------------------
class Simulation:
    """Between option 1 and 5: has step() *and* run(num_steps)."""
    def __init__(self, world, tools):
        self.world = world
        self.tools = tools
        self.t     = 0

    def step(self):
        """One synchronous tick over all agents."""
        for agent in self.world.agents:         # assumes iterable interface
            print(f"--------- {agent.name} at step {self.t} ---------")
            print(agent.description())
            if self.t == 0:
                plan = agent.generate_plan(tools=self.tools)
                #agent.add_memory("Plan: " + plan)
                print("Plan: " + plan)
            else:
                # plan = agent.generate_plan(context = "Summarize what you have attempted, then formulate your plan. Always look for something NEW to try.")
                plan = agent.generate_plan(context = "Start by summarizing what you have already done. Look for new arguments for tools you have already", tools=self.tools)
            # plan = agent.generate_plan(tools=self.tools)
            agent.add_memory("Plan: " + plan)
            # print("Plan: " + plan)

            act  = agent.generate_action(tools=self.tools)
            if act.function_calls is not None:
                for call in act.function_calls:
                    intended_action = f"Calling {call.name} with arguments {call.args}"
                    agent.add_memory("Attempting Action: " + intended_action)
                    print("Attempting Action: " + intended_action)
            else:
                print("No tools called")

            observe = self.world.model.apply_tool(act, world=self.world, agent=agent)
            for result in observe:
                agent.add_memory("Observation: " + str(result[0]))
                print("Observation: " + str(result[0]))

        self.t += 1

    def run(self, steps=1):
        for _ in range(steps):
            self.step()

# ---------- 5.  Run the demo -------------------------------------------------
sim = Simulation(world, TOOLS)
sim.run(steps=10)
world.print()