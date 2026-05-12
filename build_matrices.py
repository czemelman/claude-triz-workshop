#!/usr/bin/env python3
"""Build TRIZ matrix JSON files from extracted data."""

import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matrices')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {path}")
    return path


# ============================================================
# PARAMETERS (39 classic Altshuller parameters)
# ============================================================
PARAMETERS = {
    "1": {"name": "Weight of moving object", "description": "The mass of the object, in a gravitational field. The force that the body exerts on its support or suspension."},
    "2": {"name": "Weight of stationary object", "description": "The mass of the object, in a gravitational field. The force that the body exerts on its support or suspension, when the object is not in motion."},
    "3": {"name": "Length of moving object", "description": "Any one linear dimension of the moving object, not necessarily the longest."},
    "4": {"name": "Length of stationary object", "description": "Any one linear dimension of the stationary object, not necessarily the longest."},
    "5": {"name": "Area of moving object", "description": "A geometric characteristic described by the part of a surface enclosed within a perimeter of the moving object."},
    "6": {"name": "Area of stationary object", "description": "A geometric characteristic described by the part of a surface enclosed within a perimeter of the stationary object."},
    "7": {"name": "Volume of moving object", "description": "The cubic measure of space occupied by the moving object."},
    "8": {"name": "Volume of stationary object", "description": "The cubic measure of space occupied by the stationary object."},
    "9": {"name": "Speed", "description": "The velocity of an object; the rate of a process or action in time."},
    "10": {"name": "Force (Intensity)", "description": "Force measures the interaction between systems. In Newtonian physics force = mass x acceleration. In TRIZ force is any interaction that is intended to change an object's condition."},
    "11": {"name": "Stress or pressure", "description": "Force per unit area. Also, tension."},
    "12": {"name": "Shape", "description": "The external contours, appearance of a system."},
    "13": {"name": "Stability of the object's composition", "description": "The wholeness or integrity of the system; the relationship of the system's constituent elements. Wear, chemical decomposition, and disassembly are all decreases in stability."},
    "14": {"name": "Strength", "description": "The extent to which the object is able to resist changing in response to force. Resistance to breaking."},
    "15": {"name": "Duration of action of moving object", "description": "The time that the moving object can perform the action. Service life. Mean time between failure is a measure of the duration of action."},
    "16": {"name": "Duration of action of stationary object", "description": "The time that the stationary object can perform the action. Service life."},
    "17": {"name": "Temperature", "description": "The thermal condition of the object or system. Includes other thermal parameters, such as heat capacity, that affect the rate of change of temperature."},
    "18": {"name": "Illumination intensity", "description": "Light flux per unit area, or any other illumination characteristics of the system such as light quality, uniformity, etc."},
    "19": {"name": "Use of energy by moving object", "description": "The measure of the object's capacity for doing work. In classical mechanics, energy is the product of force x distance."},
    "20": {"name": "Use of energy by stationary object", "description": "The measure of the object's capacity for doing work when stationary."},
    "21": {"name": "Power", "description": "The time rate at which work is performed. The rate of use of energy."},
    "22": {"name": "Loss of Energy", "description": "Use of energy that does not contribute to the job being done."},
    "23": {"name": "Loss of substance", "description": "Partial or complete, permanent or temporary, loss of some of a system's material, substance, parts, or subsystems."},
    "24": {"name": "Loss of Information", "description": "Partial or complete, permanent or temporary, loss of data or access to data in or by a system."},
    "25": {"name": "Loss of Time", "description": "Time is the duration of an activity. Improving the loss of time means reducing the time taken for the activity."},
    "26": {"name": "Quantity of substance/the matter", "description": "The number or amount of a system's materials, substances, parts or subsystems."},
    "27": {"name": "Reliability", "description": "A system's ability to perform its intended functions in predictable ways and conditions."},
    "28": {"name": "Measurement accuracy", "description": "The closeness of the measured value to the actual value of a property of a system."},
    "29": {"name": "Manufacturing precision", "description": "The extent to which the actual characteristics of the system or object match the specified or required characteristics."},
    "30": {"name": "Object-affected harmful factors", "description": "Susceptibility of a system to externally generated harmful effects."},
    "31": {"name": "Object-generated harmful factors", "description": "A harmful effect is one that reduces the efficiency or quality of the functioning of the object or system."},
    "32": {"name": "Ease of manufacture", "description": "The degree of facility, comfort or effortlessness in manufacturing or fabricating the object/system."},
    "33": {"name": "Ease of operation", "description": "Simplicity: the process is NOT difficult to operate or requires excessive effort."},
    "34": {"name": "Ease of repair", "description": "Quality characteristics such as convenience, comfort, simplicity, and time to repair faults, failures, or defects in a system."},
    "35": {"name": "Adaptability or versatility", "description": "The extent to which a system/object positively responds to external changes. Also, a system that can be used in multiple ways under a variety of circumstances."},
    "36": {"name": "Device complexity", "description": "The number and diversity of elements and element interrelationships within a system."},
    "37": {"name": "Difficulty of detecting and measuring", "description": "Measuring or monitoring systems that are complex, costly, require much time and labor to set up and use, or that have complex relationships between components."},
    "38": {"name": "Extent of automation", "description": "The extent to which a system or object performs its functions without human interface."},
    "39": {"name": "Productivity", "description": "The number of functions or operations performed by a system per unit time. The output per unit time, or the cost per unit output."},
}


# ============================================================
# PRINCIPLES (40 inventive principles)
# ============================================================
PRINCIPLES = {
    "1": {"name": "Segmentation", "description": "Divide an object into independent parts.", "sub_principles": ["a) Divide an object into independent parts.", "b) Make an object easy to disassemble.", "c) Increase the degree of fragmentation or segmentation."]},
    "2": {"name": "Taking out", "description": "Separate an interfering part or property from an object, or single out the only necessary part (or property) of an object.", "sub_principles": ["a) Separate an interfering part or property from an object, or single out the only necessary part (or property) of an object."]},
    "3": {"name": "Local quality", "description": "Change an object's structure from uniform to non-uniform, change an external environment or external influence from uniform to non-uniform.", "sub_principles": ["a) Change an object's structure from uniform to non-uniform, change an external environment or external influence from uniform to non-uniform.", "b) Make each part of an object function in conditions most suitable for its operation.", "c) Make each part of an object fulfill a different and useful function."]},
    "4": {"name": "Asymmetry", "description": "Change the shape of an object from symmetrical to asymmetrical.", "sub_principles": ["a) Change the shape of an object from symmetrical to asymmetrical.", "b) If an object is asymmetrical, increase its degree of asymmetry."]},
    "5": {"name": "Merging", "description": "Bring closer together (or merge) identical or similar objects, assemble identical or similar parts to perform parallel operations.", "sub_principles": ["a) Bring closer together (or merge) identical or similar objects, assemble identical or similar parts to perform parallel operations.", "b) Make operations contiguous or parallel; bring them together in time."]},
    "6": {"name": "Universality", "description": "Make a part or object perform multiple functions; eliminate the need for other parts.", "sub_principles": ["a) Make a part or object perform multiple functions; eliminate the need for other parts."]},
    "7": {"name": "Nested doll", "description": "Place one object inside another; place each object, in turn, inside the other.", "sub_principles": ["a) Place one object inside another; place each object, in turn, inside the other.", "b) Make one part pass through a cavity in the other."]},
    "8": {"name": "Anti-weight", "description": "To compensate for the weight of an object, merge it with other objects that provide lift.", "sub_principles": ["a) To compensate for the weight of an object, merge it with other objects that provide lift.", "b) To compensate for the weight of an object, make it interact with the environment (e.g. use aerodynamic, hydrodynamic, buoyancy and other forces)."]},
    "9": {"name": "Preliminary anti-action", "description": "If it will be necessary to do an action with both harmful and useful effects, this action should be replaced with anti-actions to control harmful effects.", "sub_principles": ["a) If it will be necessary to do an action with both harmful and useful effects, this action should be replaced with anti-actions to control harmful effects.", "b) Create beforehand stresses in an object that will oppose known undesirable working stresses later on."]},
    "10": {"name": "Preliminary action", "description": "Perform, before it is needed, the required change of an object (either fully or partially).", "sub_principles": ["a) Perform, before it is needed, the required change of an object (either fully or partially).", "b) Pre-arrange objects such that they can come into action from the most convenient place and without losing time for their delivery."]},
    "11": {"name": "Beforehand cushioning", "description": "Prepare emergency means beforehand to compensate for the relatively low reliability of an object.", "sub_principles": ["a) Prepare emergency means beforehand to compensate for the relatively low reliability of an object."]},
    "12": {"name": "Equipotentiality", "description": "In a potential field, limit position changes (e.g. change operating conditions to eliminate the need to raise or lower objects in a gravity field).", "sub_principles": ["a) In a potential field, limit position changes (e.g. change operating conditions to eliminate the need to raise or lower objects in a gravity field)."]},
    "13": {"name": "The other way round", "description": "Invert the action(s) used to solve the problem.", "sub_principles": ["a) Invert the action(s) used to solve the problem (e.g. instead of cooling an object, heat it).", "b) Make movable parts (or the external environment) fixed, and fixed parts movable.", "c) Turn the object (or process) upside down."]},
    "14": {"name": "Spheroidality - Loss of curvature", "description": "Instead of using rectilinear parts, surfaces, or forms, use curvilinear ones; move from flat surfaces to spherical ones; from parts shaped as a cube (parallelepiped) to ball-shaped structures.", "sub_principles": ["a) Instead of using rectilinear parts, surfaces, or forms, use curvilinear ones; move from flat surfaces to spherical ones.", "b) Use rollers, balls, spirals, domes.", "c) Go from linear to rotary motion, use centrifugal forces."]},
    "15": {"name": "Dynamics", "description": "Allow (or design) the characteristics of an object, external environment, or process to change to be optimal or to find an optimal operating condition.", "sub_principles": ["a) Allow (or design) the characteristics of an object, external environment, or process to change to be optimal or to find an optimal operating condition.", "b) Divide an object into parts capable of movement relative to each other.", "c) If an object (or process) is rigid or inflexible, make it movable or adaptive."]},
    "16": {"name": "Partial or excessive actions", "description": "If 100 percent of an object is hard to achieve using a given solution method then, by using 'slightly less' or 'slightly more' of the same method, the problem may be considerably easier to solve.", "sub_principles": ["a) If 100 percent of an object is hard to achieve using a given solution method then, by using 'slightly less' or 'slightly more' of the same method, the problem may be considerably easier to solve."]},
    "17": {"name": "Another dimension", "description": "To move an object in two- or three-dimensional space.", "sub_principles": ["a) To move an object in two- or three-dimensional space.", "b) Use a multi-story arrangement of objects instead of a single-story arrangement.", "c) Tilt or re-orient the object, lay it on its side.", "d) Use another side of a given area."]},
    "18": {"name": "Mechanical vibration", "description": "Cause an object to oscillate or vibrate.", "sub_principles": ["a) Cause an object to oscillate or vibrate.", "b) Increase its frequency (even up to the ultrasonic).", "c) Use an object's resonant frequency.", "d) Use piezoelectric vibrators instead of mechanical ones.", "e) Use combined ultrasonic and electromagnetic field oscillations."]},
    "19": {"name": "Periodic action", "description": "Instead of continuous action, use periodic or pulsating actions.", "sub_principles": ["a) Instead of continuous action, use periodic or pulsating actions.", "b) If an action is already periodic, change the periodic magnitude or frequency.", "c) Use pauses between impulses to perform a different action."]},
    "20": {"name": "Continuity of useful action", "description": "Carry on work continuously; make all parts of an object work at full load, all the time.", "sub_principles": ["a) Carry on work continuously; make all parts of an object work at full load, all the time.", "b) Eliminate all idle or intermittent actions or work."]},
    "21": {"name": "Skipping", "description": "Conduct a process, or certain stages (e.g. destructible, harmful or hazardous operations) at high speed.", "sub_principles": ["a) Conduct a process, or certain stages (e.g. destructible, harmful or hazardous operations) at high speed."]},
    "22": {"name": "Blessing in disguise", "description": "Use harmful factors (particularly, harmful effects of the environment or surroundings) to achieve a positive effect.", "sub_principles": ["a) Use harmful factors (particularly, harmful effects of the environment or surroundings) to achieve a positive effect.", "b) Eliminate the primary harmful action by adding it to another harmful action to resolve the problem.", "c) Amplify a harmful factor to such a degree that it is no longer harmful."]},
    "23": {"name": "Feedback", "description": "Introduce feedback (referring back, cross-checking) to improve a process or action.", "sub_principles": ["a) Introduce feedback (referring back, cross-checking) to improve a process or action.", "b) If feedback is already used, change its magnitude or influence."]},
    "24": {"name": "Intermediary", "description": "Use an intermediary carrier article or intermediary process.", "sub_principles": ["a) Use an intermediary carrier article or intermediary process.", "b) Merge one object temporarily with another (which can be easily removed)."]},
    "25": {"name": "Self-service", "description": "Make an object serve itself by performing auxiliary helpful functions.", "sub_principles": ["a) Make an object serve itself by performing auxiliary helpful functions.", "b) Use waste resources, energy, or substances."]},
    "26": {"name": "Copying", "description": "Instead of an unavailable, expensive, fragile object, use simpler and inexpensive copies.", "sub_principles": ["a) Instead of an unavailable, expensive, fragile object, use simpler and inexpensive copies.", "b) Replace an object, or process with optical copies.", "c) If visible optical copies are already used, move to infrared or ultraviolet copies."]},
    "27": {"name": "Cheap short-living objects", "description": "Replace an inexpensive object with a multiple of inexpensive objects, comprising certain qualities (such as service life, for instance).", "sub_principles": ["a) Replace an inexpensive object with a multiple of inexpensive objects, comprising certain qualities (such as service life, for instance)."]},
    "28": {"name": "Mechanics substitution", "description": "Replace a mechanical means with a sensory (optical, acoustic, taste or smell) means.", "sub_principles": ["a) Replace a mechanical means with a sensory (optical, acoustic, taste or smell) means.", "b) Use electric, magnetic and electromagnetic fields to interact with the object.", "c) Change from static to movable fields, from unstructured fields to those having structure.", "d) Use fields in conjunction with field-activated (e.g. ferromagnetic) particles."]},
    "29": {"name": "Pneumatics and hydraulics", "description": "Use gas and liquid parts of an object instead of solid parts (e.g. inflatable and filled, air cushion, hydrostatic, hydro-reactive).", "sub_principles": ["a) Use gas and liquid parts of an object instead of solid parts (e.g. inflatable and filled, air cushion, hydrostatic, hydro-reactive)."]},
    "30": {"name": "Flexible shells and thin films", "description": "Use flexible shells and thin films instead of three dimensional structures.", "sub_principles": ["a) Use flexible shells and thin films instead of three dimensional structures.", "b) Isolate the object from the external environment using flexible shells and thin films."]},
    "31": {"name": "Porous materials", "description": "Make an object porous or add porous elements (inserts, coatings, etc.).", "sub_principles": ["a) Make an object porous or add porous elements (inserts, coatings, etc.).", "b) If an object is already porous, use the pores to introduce a useful substance or function."]},
    "32": {"name": "Color changes", "description": "Change the color of an object or its external environment.", "sub_principles": ["a) Change the color of an object or its external environment.", "b) Change the transparency of an object or its external environment."]},
    "33": {"name": "Homogeneity", "description": "Make objects interacting with a given object of the same material (or material with identical properties).", "sub_principles": ["a) Make objects interacting with a given object of the same material (or material with identical properties)."]},
    "34": {"name": "Discarding and recovering", "description": "Make portions of an object that have fulfilled their functions go away (discard by dissolving, evaporating, etc.) or modify these directly during operation.", "sub_principles": ["a) Make portions of an object that have fulfilled their functions go away (discard by dissolving, evaporating, etc.) or modify these directly during operation.", "b) Conversely, restore consumable parts of an object directly in operation."]},
    "35": {"name": "Parameter changes", "description": "Change an object's physical state (e.g. to a gas, liquid, or solid).", "sub_principles": ["a) Change an object's physical state (e.g. to a gas, liquid, or solid).", "b) Change the concentration or consistency.", "c) Change the degree of flexibility.", "d) Change the temperature."]},
    "36": {"name": "Phase transitions", "description": "Use phenomena occurring during phase transitions (e.g. volume changes, loss or absorption of heat, etc.).", "sub_principles": ["a) Use phenomena occurring during phase transitions (e.g. volume changes, loss or absorption of heat, etc.)."]},
    "37": {"name": "Thermal expansion", "description": "Use thermal expansion (or contraction) of materials.", "sub_principles": ["a) Use thermal expansion (or contraction) of materials.", "b) If thermal expansion is being used, use multiple materials with different coefficients of thermal expansion."]},
    "38": {"name": "Strong oxidants", "description": "Replace common air with oxygen-enriched air.", "sub_principles": ["a) Replace common air with oxygen-enriched air.", "b) Replace enriched air with pure oxygen.", "c) Expose air or oxygen to ionizing radiation.", "d) Use ionized oxygen.", "e) Replace ozonized (or ionized) oxygen with ozone."]},
    "39": {"name": "Inert atmosphere", "description": "Replace a normal environment with an inert one.", "sub_principles": ["a) Replace a normal environment with an inert one.", "b) Add neutral parts, or inert additives to an object."]},
    "40": {"name": "Composite materials", "description": "Change from uniform to composite (multiple) materials.", "sub_principles": ["a) Change from uniform to composite (multiple) materials."]},
}


# ============================================================
# CLASSIC 39x39 MATRIX DATA (from triz40.com)
# ============================================================
# Format: (improving, worsening): [principle IDs]
MATRIX_RAW = {
    # Row 1
    (1,3): [15,8,29,34], (1,5): [29,17,38,34], (1,7): [29,2,40,28],
    (1,9): [2,8,15,38], (1,10): [8,10,18,37], (1,11): [10,36,37,40],
    (1,12): [10,14,35,40], (1,13): [1,35,19,39], (1,14): [28,27,18,40],
    (1,15): [5,34,31,35], (1,17): [6,29,4,38], (1,18): [19,1,32],
    (1,19): [35,12,34,31], (1,20): [12,36,18,31], (1,21): [6,2,34,19],
    (1,22): [5,35,3,31], (1,23): [10,24,35], (1,24): [10,35,20,28],
    (1,25): [3,26,18,31], (1,26): [1,3,11,27], (1,27): [28,27,35,26],
    (1,28): [28,35,26,18], (1,29): [22,21,18,27], (1,30): [22,35,31,39],
    (1,31): [27,28,1,36], (1,32): [35,3,2,24], (1,33): [2,27,28,11],
    (1,34): [29,5,15,8], (1,35): [26,30,36,34], (1,36): [28,29,26,32],
    (1,37): [26,35,18,19], (1,38): [35,3,24,37],
    # Row 2
    (2,4): [10,1,29,35], (2,6): [35,30,13,2], (2,8): [5,35,14,2],
    (2,10): [8,10,19,35], (2,11): [13,29,10,18], (2,12): [13,10,29,14],
    (2,13): [26,39,1,40], (2,14): [28,2,10,27], (2,16): [2,27,19,6],
    (2,17): [28,19,32,22], (2,18): [19,32,35], (2,20): [18,19,28,1],
    (2,21): [15,19,18,22], (2,22): [18,19,28,15], (2,23): [5,8,13,30],
    (2,24): [10,15,35], (2,25): [10,20,35,26], (2,26): [19,6,18,26],
    (2,27): [10,28,8,3], (2,28): [18,26,28], (2,29): [10,1,35,17],
    (2,30): [2,19,22,37], (2,31): [35,22,1,39], (2,32): [28,1,9],
    (2,33): [6,13,1,32], (2,34): [2,27,28,11], (2,35): [19,15,29],
    (2,36): [1,10,26,39], (2,37): [25,28,17,15], (2,38): [2,26,35],
    (2,39): [1,28,15,35],
    # Row 3
    (3,1): [8,15,29,34], (3,4): [15,17,4], (3,6): [7,17,4,35],
    (3,8): [13,4,8], (3,9): [17,10,4], (3,10): [1,8,35],
    (3,11): [1,8,10,29], (3,12): [8,35,29,34], (3,13): [19],
    (3,15): [10,15,19], (3,16): [32], (3,17): [8,35,24],
    (3,19): [1,35], (3,20): [7,2,35,39], (3,21): [4,29,23,10],
    (3,22): [1,24], (3,23): [15,2,29], (3,24): [29,35],
    (3,25): [10,14,29,40], (3,26): [28,32,4], (3,27): [10,28,29,37],
    (3,28): [1,15,17,24], (3,29): [17,15], (3,30): [1,29,17],
    (3,31): [15,29,35,4], (3,32): [1,28,10], (3,33): [14,15,1,16],
    (3,34): [1,19,26,24], (3,35): [35,1,26,24], (3,36): [17,24,26,16],
    (3,37): [14,4,28,29], (3,39): [30,14,7,26],
    # Row 4
    (4,2): [35,28,40,29], (4,5): [17,7,10,40], (4,7): [35,8,2,14],
    (4,9): [28,10], (4,10): [1,14,35], (4,11): [13,14,15,7],
    (4,12): [39,37,35], (4,13): [15,14,28,26], (4,15): [1,10,35],
    (4,16): [3,35,38,18], (4,17): [3,25], (4,20): [12,8],
    (4,21): [6,28], (4,22): [10,28,24,35], (4,23): [24,26],
    (4,24): [30,29,14], (4,26): [15,29,28], (4,27): [32,28,3],
    (4,28): [2,32,10], (4,29): [1,18], (4,31): [15,17,27],
    (4,32): [2,25], (4,33): [3], (4,34): [1,35], (4,35): [1,26],
    (4,36): [26], (4,38): [30,14,7,26],
    # Row 5
    (5,1): [2,17,29,4], (5,3): [14,15,18,4], (5,6): [7,14,17,4],
    (5,8): [29,30,4,34], (5,9): [19,30,35,2], (5,10): [10,15,36,28],
    (5,11): [5,34,29,4], (5,12): [11,2,13,39], (5,13): [3,15,40,14],
    (5,14): [6,3], (5,16): [2,15,16], (5,17): [15,32,19,13],
    (5,18): [19,32], (5,20): [19,10,32,18], (5,21): [15,17,30,26],
    (5,22): [10,35,2,39], (5,23): [30,26], (5,24): [26,4],
    (5,25): [29,30,6,13], (5,26): [29,9], (5,27): [26,28,32,3],
    (5,28): [2,32], (5,29): [22,33,28,1], (5,30): [17,2,18,39],
    (5,31): [13,1,26,24], (5,32): [15,17,13,16], (5,33): [15,13,10,1],
    (5,34): [15,30], (5,35): [14,1,13], (5,36): [2,36,26,18],
    (5,37): [14,30,28,23], (5,38): [10,26,34,2],
    # Row 6
    (6,2): [30,2,14,18], (6,4): [26,7,9,39], (6,9): [1,18,35,36],
    (6,10): [10,15,36,37], (6,12): [2,38], (6,13): [40],
    (6,15): [2,10,19,30], (6,16): [35,39,38], (6,20): [17,32],
    (6,21): [17,7,30], (6,22): [10,14,18,39], (6,23): [30,16],
    (6,24): [10,35,4,18], (6,25): [2,18,40,4], (6,26): [32,35,40,4],
    (6,27): [26,28,32,3], (6,28): [2,29,18,36], (6,29): [27,2,39,35],
    (6,30): [22,1,40], (6,31): [40,16], (6,32): [16,4], (6,33): [16],
    (6,34): [15,16], (6,35): [1,18,36], (6,36): [2,35,30,18],
    (6,37): [23], (6,38): [10,15,17,7],
    # Row 7
    (7,1): [2,26,29,40], (7,3): [1,7,4,35], (7,5): [1,7,4,17],
    (7,8): [29,4,38,34], (7,9): [15,35,36,37], (7,10): [6,35,36,37],
    (7,11): [1,15,29,4], (7,12): [28,10,1,39], (7,13): [9,14,15,7],
    (7,14): [6,35,4], (7,16): [34,39,10,18], (7,17): [2,13,10],
    (7,18): [35], (7,20): [35,6,13,18], (7,21): [7,15,13,16],
    (7,22): [36,39,34,10], (7,23): [2,22], (7,24): [2,6,34,10],
    (7,25): [29,30,7], (7,26): [14,1,40,11], (7,27): [25,26,28],
    (7,28): [25,28,2,16], (7,29): [22,21,27,35], (7,30): [17,2,40,1],
    (7,31): [29,1,40], (7,32): [15,13,30,12], (7,33): [10],
    (7,34): [15,29], (7,35): [26,1], (7,36): [29,26,4],
    (7,37): [35,34,16,24], (7,38): [10,6,2,34],
    # Row 8
    (8,2): [35,10,19,14], (8,3): [19,14], (8,4): [35,8,2,14],
    (8,9): [2,18,37], (8,10): [24,35], (8,11): [7,2,35],
    (8,12): [34,28,35,40], (8,13): [9,14,17,15], (8,15): [35,34,38],
    (8,16): [35,6,4], (8,20): [30,6], (8,22): [10,39,35,34],
    (8,24): [35,16,32,18], (8,25): [35,3], (8,26): [2,35,16],
    (8,28): [35,10,25], (8,29): [34,39,19,27], (8,30): [30,18,35,4],
    (8,31): [35], (8,33): [1], (8,35): [1,31], (8,36): [2,17,26],
    (8,38): [35,37,10,2],
    # Row 9
    (9,1): [2,28,13,38], (9,3): [13,14,8], (9,5): [29,30,34],
    (9,7): [7,29,34], (9,10): [13,28,15,19], (9,11): [6,18,38,40],
    (9,12): [35,15,18,34], (9,13): [28,33,1,18], (9,14): [8,3,26,14],
    (9,15): [3,19,35,5], (9,17): [28,30,36,2], (9,18): [10,13,19],
    (9,19): [8,15,35,38], (9,21): [19,35,38,2], (9,22): [14,20,19,35],
    (9,23): [10,13,28,38], (9,24): [13,26], (9,26): [10,19,29,38],
    (9,27): [11,35,27,28], (9,28): [28,32,1,24], (9,29): [10,28,32,25],
    (9,30): [1,28,35,23], (9,31): [2,24,35,21], (9,32): [35,13,8,1],
    (9,33): [32,28,13,12], (9,34): [34,2,28,27], (9,35): [15,10,26],
    (9,36): [10,28,4,34], (9,37): [3,34,27,16], (9,38): [10,18],
    # Row 10
    (10,1): [8,1,37,18], (10,2): [18,13,1,28], (10,3): [17,19,9,36],
    (10,4): [28,10], (10,5): [19,10,15], (10,6): [1,18,36,37],
    (10,7): [15,9,12,37], (10,8): [2,36,18,37], (10,9): [13,28,15,12],
    (10,11): [18,21,11], (10,12): [10,35,40,34], (10,13): [35,10,21],
    (10,14): [35,10,14,27], (10,15): [19,2], (10,17): [35,10,21],
    (10,19): [19,17,10], (10,20): [1,16,36,37], (10,21): [19,35,18,37],
    (10,22): [14,15], (10,23): [8,35,40,5], (10,25): [10,37,36],
    (10,26): [14,29,18,36], (10,27): [3,35,13,21], (10,28): [35,10,23,24],
    (10,29): [28,29,37,36], (10,30): [1,35,40,18], (10,31): [13,3,36,24],
    (10,32): [15,37,18,1], (10,33): [1,28,3,25], (10,34): [15,1,11],
    (10,35): [15,17,18,20], (10,36): [26,35,10,18], (10,37): [36,37,10,19],
    (10,38): [2,35], (10,39): [3,28,35,37],
    # Row 11
    (11,1): [10,36,37,40], (11,2): [13,29,10,18], (11,3): [35,10,36],
    (11,4): [35,1,14,16], (11,5): [10,15,36,28], (11,6): [10,15,36,37],
    (11,7): [6,35,10], (11,8): [35,24], (11,9): [6,35,36],
    (11,10): [36,35,21], (11,12): [35,4,15,10], (11,13): [35,33,2,40],
    (11,14): [9,18,3,40], (11,15): [19,3,27], (11,17): [35,39,19,2],
    (11,19): [14,24,10,37], (11,21): [10,35,14], (11,22): [2,36,25],
    (11,23): [10,36,3,37], (11,25): [37,36,4], (11,26): [10,14,36],
    (11,27): [10,13,19,35], (11,28): [6,28,25], (11,29): [3,35],
    (11,30): [22,2,37], (11,31): [2,33,27,18], (11,32): [1,35,16],
    (11,33): [11], (11,34): [2], (11,35): [35], (11,36): [19,1,35],
    (11,37): [2,36,37], (11,38): [35,24], (11,39): [10,14,35,37],
    # Row 12
    (12,1): [8,10,29,40], (12,2): [15,10,26,3], (12,3): [29,34,5,4],
    (12,4): [13,14,10,7], (12,5): [5,34,4,10], (12,7): [14,4,15,22],
    (12,8): [7,2,35], (12,9): [35,15,18,34], (12,10): [35,10,37,40],
    (12,11): [34,15,10,14], (12,13): [33,1,18,4], (12,14): [30,14,10,40],
    (12,15): [14,26,9,25], (12,17): [22,14,19,32], (12,18): [13,15,32],
    (12,19): [2,6,34,14], (12,21): [4,6,2], (12,22): [14],
    (12,23): [35,29,3,5], (12,25): [14,10,34,17], (12,26): [36,22],
    (12,29): [32,30,40], (12,30): [22,1,2,35], (12,31): [35,1],
    (12,32): [1,32,17,28], (12,33): [32,15,26], (12,34): [2,13,1],
    (12,35): [1,15,29], (12,36): [16,29,1,28], (12,37): [15,13,39],
    (12,38): [15,1,32], (12,39): [17,26,34,10],
    # Row 13
    (13,1): [21,35,2,39], (13,2): [26,39,1,40], (13,3): [13,15,1,28],
    (13,4): [37], (13,5): [2,11,13], (13,6): [39], (13,7): [28,10,19,39],
    (13,8): [34,28,35,40], (13,9): [33,15,28,18], (13,10): [10,35,21,16],
    (13,11): [2,35,40], (13,12): [22,1,18,4], (13,14): [17,9,15],
    (13,15): [13,27,10,35], (13,16): [39,3,35,23], (13,17): [35,1,32],
    (13,18): [32,3,27,16], (13,19): [13,19], (13,20): [27,4,29,18],
    (13,21): [32,35,27,31], (13,22): [14,2,39,6], (13,23): [2,14,30,40],
    (13,25): [35,27], (13,26): [15,32,35], (13,27): [35,27],
    (13,28): [13], (13,29): [18], (13,30): [35,24,30,18],
    (13,31): [35,40,27,39], (13,32): [35,19], (13,33): [32,35,30],
    (13,34): [2,35,10,16], (13,35): [35,30,34,2], (13,36): [2,35,22,26],
    (13,37): [35,22,39,23], (13,38): [1,8,35], (13,39): [23,35,40,3],
    # Row 14
    (14,1): [1,8,40,15], (14,2): [40,26,27,1], (14,3): [1,15,8,35],
    (14,4): [15,14,28,26], (14,5): [3,34,40,29], (14,6): [9,40,28],
    (14,7): [10,15,14,7], (14,8): [9,14,17,15], (14,9): [8,13,26,14],
    (14,10): [10,18,3,14], (14,11): [10,3,18,40], (14,12): [10,30,35,40],
    (14,13): [13,17,35], (14,15): [27,3,26], (14,17): [30,10,40],
    (14,18): [35,19], (14,19): [19,35,10], (14,20): [35],
    (14,21): [10,26,35,28], (14,22): [35], (14,23): [35,28,31,40],
    (14,25): [29,3,28,10], (14,26): [29,10,27], (14,27): [11,3],
    (14,28): [3,27,16], (14,29): [3,27], (14,30): [18,35,37,1],
    (14,31): [15,35,22,2], (14,32): [11,3,10,32], (14,33): [32,40,25,2],
    (14,34): [27,11,3], (14,35): [15,3,32], (14,36): [2,13,25,28],
    (14,37): [27,3,15,40], (14,38): [15], (14,39): [29,35,10,14],
    # Row 15
    (15,1): [19,5,34,31], (15,3): [2,19,9], (15,5): [3,17,19],
    (15,7): [10,2,19,30], (15,9): [3,35,5], (15,10): [19,2,16],
    (15,11): [19,3,27], (15,12): [14,26,28,25], (15,13): [13,3,35],
    (15,14): [27,3,10], (15,17): [19,35,39], (15,18): [2,19,4,35],
    (15,19): [28,6,35,18], (15,20): [10], (15,21): [20,10,28,18],
    (15,22): [3,35,10,40], (15,23): [11,2,13], (15,24): [3],
    (15,25): [3,27,16,40], (15,26): [22,15,33,28], (15,27): [21,39,16,22],
    (15,28): [27,1,4], (15,29): [12,27], (15,30): [29,10,27],
    (15,31): [1,35,13], (15,32): [10,4,29,15], (15,33): [19,29,39,35],
    (15,34): [6,10], (15,35): [35,17,14,19], (15,36): [15,1],
    (15,37): [6], (15,38): [35,17,14,19], (15,39): [15],
    # Row 16
    (16,2): [6,27,19,16], (16,4): [1,40,35], (16,8): [35,34,38],
    (16,12): [39,3,35,23], (16,15): [19,18,36,40], (16,19): [16],
    (16,21): [27,16,18,38], (16,22): [10], (16,23): [28,20,10,16],
    (16,24): [3,35,31], (16,25): [34,27,6,40], (16,26): [10,26,24],
    (16,28): [17,1,40,33], (16,29): [22], (16,30): [35,10],
    (16,31): [1], (16,32): [1], (16,33): [2], (16,35): [25,34,6,35],
    (16,37): [20,10,16,38],
    # Row 17
    (17,1): [36,22,6,38], (17,2): [22,35,32], (17,3): [15,19,9],
    (17,4): [15,19,9], (17,5): [3,35,39,18], (17,6): [35,38],
    (17,7): [34,39,40,18], (17,8): [35,6,4], (17,9): [2,28,36,30],
    (17,10): [35,10,3,21], (17,11): [35,39,19,2], (17,12): [14,22,19,32],
    (17,13): [1,35,32], (17,14): [10,30,22,40], (17,15): [19,13,39],
    (17,16): [19,18,36,40], (17,18): [32,30,21,16], (17,19): [19,15,3,17],
    (17,20): [2,14,17,25], (17,21): [21,17,35,38], (17,22): [21,36,29,31],
    (17,25): [35,28,21,18], (17,26): [3,17,30,39], (17,27): [19,35,3,10],
    (17,28): [32,19,24], (17,29): [24], (17,30): [22,33,35,2],
    (17,31): [22,35,2,24], (17,32): [26,27], (17,33): [26,27],
    (17,34): [4,10,16], (17,35): [2,18,27], (17,36): [2,17,16],
    (17,37): [3,27,35,31], (17,38): [26,2,19,16], (17,39): [15,28,35],
    # Row 18
    (18,1): [19,1,32], (18,2): [2,35,32], (18,3): [19,32,16],
    (18,5): [19,32,26], (18,7): [2,13,10], (18,9): [10,13,19],
    (18,10): [26,19,6], (18,12): [32,30], (18,13): [32,3,27],
    (18,14): [35,19], (18,15): [2,19,6], (18,17): [32,35,19],
    (18,19): [32,1,19], (18,20): [32,35,1,15], (18,21): [32],
    (18,22): [13,16,1,6], (18,23): [13,1], (18,24): [1,6],
    (18,25): [19,1,26,17], (18,26): [1,19], (18,28): [11,15,32],
    (18,29): [3,32], (18,30): [15,19], (18,31): [35,19,32,39],
    (18,32): [19,35,28,26], (18,33): [28,26,19], (18,34): [15,17,13,16],
    (18,35): [15,1,19], (18,36): [6,32,13], (18,37): [32,15],
    (18,38): [2,26,10], (18,39): [2,25,16],
    # Row 19
    (19,1): [12,18,28,31], (19,3): [12,28], (19,5): [15,19,25],
    (19,7): [35,13,18], (19,9): [8,35], (19,10): [16,26,21,2],
    (19,11): [23,14,25], (19,12): [12,2,29], (19,13): [19,13,17,24],
    (19,14): [5,19,9,35], (19,15): [28,6,35,18], (19,17): [19,24,3,14],
    (19,18): [2,15,19], (19,20): [6,19,37,18], (19,21): [12,22,15,24],
    (19,22): [35,24,18,5], (19,24): [35,38,19,18], (19,25): [34,23,16,18],
    (19,26): [19,21,11,27], (19,27): [3,1,32], (19,29): [1,35,6,27],
    (19,30): [2,35,6], (19,31): [28,26,30], (19,32): [19,35],
    (19,33): [1,15,17,28], (19,34): [15,17,13,16], (19,35): [2,29,27,28],
    (19,36): [35,38], (19,37): [32,2], (19,38): [12,28,35],
    # Row 20
    (20,2): [19,9,6,27], (20,10): [36,37], (20,13): [27,4,29,18],
    (20,14): [35], (20,18): [19,2,35,32], (20,21): [28,27,18,31],
    (20,24): [3,35,31], (20,25): [10,36,23], (20,28): [10,2,22,37],
    (20,29): [19,22,18], (20,30): [1,4], (20,33): [10,2,22,37],
    (20,34): [19,22,18], (20,35): [1,4], (20,39): [19,35,16,25],
    # Row 21
    (21,1): [8,36,38,31], (21,2): [19,26,17,27], (21,3): [1,10,35,37],
    (21,5): [19,38], (21,6): [17,32,13,38], (21,7): [35,6,38],
    (21,8): [30,6,25], (21,9): [15,35,2], (21,10): [26,2,36,35],
    (21,11): [22,10,35], (21,12): [29,14,2,40], (21,13): [35,32,15,31],
    (21,14): [26,10,28], (21,15): [19,35,10,38], (21,17): [16,6,19],
    (21,18): [16,6,19,37], (21,20): [10,35,38], (21,22): [28,27,18,38],
    (21,23): [10,19], (21,24): [35,20,10,6], (21,25): [4,34,19],
    (21,26): [19,24,26,31], (21,27): [32,15,2], (21,28): [32,2],
    (21,29): [19,22,31,2], (21,30): [2,35,18], (21,31): [26,10,34],
    (21,32): [26,35,10], (21,33): [35,2,10,34], (21,34): [19,17,34],
    (21,35): [20,19,30,34], (21,36): [19,35,16], (21,37): [28,2,17],
    (21,38): [28,35,34], (21,39): [28,35,34],
    # Row 22
    (22,1): [15,6,19,28], (22,2): [19,6,18,9], (22,3): [7,2,6,13],
    (22,4): [6,38,7], (22,5): [15,26,17,30], (22,6): [17,7,30,18],
    (22,7): [7,18,23], (22,8): [7], (22,9): [16,35,38],
    (22,10): [36,38], (22,13): [14,2,39,6], (22,14): [26],
    (22,17): [19,38,7], (22,18): [1,13,32,15], (22,23): [3,38],
    (22,24): [35,27,2,37], (22,25): [19,10], (22,26): [10,18,32,7],
    (22,27): [7,18,25], (22,28): [11,10,35], (22,30): [32],
    (22,32): [21,22,35,2], (22,33): [21,35,2,22], (22,35): [35,32,1],
    (22,36): [2,19], (22,37): [2], (22,38): [7,23],
    (22,39): [35,3,15,23],
    # Row 23
    (23,1): [35,6,23,40], (23,2): [35,6,22,32], (23,3): [14,29,10,39],
    (23,4): [10,28,24], (23,5): [35,2,10,31], (23,6): [10,18,39,31],
    (23,7): [1,29,30,36], (23,8): [3,39,18,31], (23,9): [10,13,28,38],
    (23,10): [14,15,18,40], (23,11): [3,36,37,10], (23,12): [29,35,3,5],
    (23,13): [2,14,30,40], (23,14): [35,28,31,40], (23,15): [28,27,3,18],
    (23,16): [27,16,18,38], (23,17): [21,36,39,31], (23,18): [1,6,13],
    (23,19): [35,18,24,5], (23,20): [28,27,12,31], (23,21): [28,27,18,38],
    (23,24): [35,27,2,31], (23,25): [15,18,35,10], (23,26): [6,3,10,24],
    (23,27): [10,29,39,35], (23,28): [16,34,31,28], (23,29): [35,10,24,31],
    (23,30): [33,22,30,40], (23,31): [10,1,34,29], (23,32): [15,34,33],
    (23,33): [32,28,2,24], (23,34): [2,35,34,27], (23,35): [15,10,2],
    (23,36): [35,10,28,24], (23,37): [35,18,10,13], (23,38): [35,10,18],
    (23,39): [28,35,10,23],
    # Row 24
    (24,1): [10,24,35], (24,2): [10,35,5], (24,3): [1,26],
    (24,4): [26], (24,5): [30,26], (24,6): [30,16], (24,13): [10],
    (24,14): [10], (24,18): [19], (24,25): [10,19], (24,26): [19,10],
    (24,27): [10,30,4], (24,28): [24,26,28,32], (24,29): [24,28,35],
    (24,30): [10,28,23], (24,32): [22,10,1], (24,33): [10,21,22],
    (24,34): [32], (24,35): [27,22], (24,36): [35,33], (24,37): [35],
    (24,39): [13,23,15],
    # Row 25
    (25,1): [10,20,37,35], (25,2): [10,20,26,5], (25,3): [15,2,29],
    (25,4): [30,24,14,5], (25,5): [26,4,5,16], (25,6): [10,35,17,4],
    (25,7): [2,5,34,10], (25,8): [35,16,32,18], (25,10): [10,37,36,5],
    (25,11): [37,36,4], (25,12): [4,10,34,17], (25,13): [35,3,22,5],
    (25,14): [29,3,28,18], (25,15): [20,10,28,18], (25,16): [28,20,10,16],
    (25,17): [35,29,21,18], (25,18): [1,19,26,17], (25,19): [35,38,19,18],
    (25,21): [1], (25,23): [35,20,10,6], (25,24): [10,5,18,32],
    (25,26): [35,18,10,39], (25,27): [24,26,28,32], (25,28): [35,38,18,16],
    (25,29): [10,30,4], (25,30): [24,34,28,32], (25,31): [24,26,28,18],
    (25,32): [35,18,34], (25,33): [35,22,18,39], (25,34): [35,28,34,4],
    (25,35): [4,28,10,34], (25,36): [32,1,10], (25,37): [35,28],
    (25,38): [6,29], (25,39): [18,28,32,10],
    # Row 26
    (26,1): [35,6,18,31], (26,2): [27,26,18,35], (26,3): [29,14,35,18],
    (26,5): [15,14,29], (26,6): [2,18,40,4], (26,7): [15,20,29],
    (26,9): [35,29,34,28], (26,10): [35,14,3], (26,11): [10,36,14,3],
    (26,12): [35,14], (26,13): [15,2,17,40], (26,14): [14,35,34,10],
    (26,15): [3,35,10,40], (26,16): [3,35,31], (26,17): [3,17,39],
    (26,19): [34,29,16,18], (26,20): [3,35,31], (26,21): [35],
    (26,22): [7,18,25], (26,23): [6,3,10,24], (26,24): [24,28,35],
    (26,25): [35,38,18,16], (26,27): [18,3,28,40], (26,28): [13,2,28],
    (26,29): [33,30], (26,30): [35,33,29,31], (26,31): [3,35,40,39],
    (26,32): [29,1,35,27], (26,33): [35,29,25,10], (26,34): [2,32,10,25],
    (26,35): [15,3,29], (26,36): [3,13,27,10], (26,37): [3,27,29,18],
    (26,38): [8,35], (26,39): [13,29,3,27],
    # Row 27
    (27,1): [3,8,10,40], (27,2): [3,10,8,28], (27,3): [15,9,14,4],
    (27,4): [15,29,28,11], (27,5): [17,10,14,16], (27,6): [32,35,40,4],
    (27,7): [3,10,14,24], (27,8): [2,35,24], (27,9): [21,35,11,28],
    (27,10): [8,28,10,3], (27,11): [10,24,35,19], (27,12): [35,1,16,11],
    (27,14): [11,28], (27,15): [2,35,3,25], (27,16): [34,27,6,40],
    (27,17): [3,35,10], (27,18): [11,32,13], (27,19): [21,11,27,19],
    (27,20): [36,23], (27,21): [21,11,26,31], (27,22): [10,11,35],
    (27,24): [10,35,29,39], (27,25): [10,28], (27,26): [10,30,4],
    (27,28): [21,28,40,3], (27,29): [32,3,11,23], (27,30): [11,32,1],
    (27,31): [27,35,2,40], (27,32): [35,2,40,26], (27,34): [27,17,40],
    (27,35): [1,11], (27,36): [13,35,8,24], (27,37): [13,35,1],
    (27,38): [27,40,28], (27,39): [11,13,27],
    # Row 28
    (28,1): [32,35,26,28], (28,2): [28,35,25,26], (28,3): [28,26,5,16],
    (28,4): [32,28,3,16], (28,5): [26,28,32,3], (28,6): [26,28,32,3],
    (28,7): [32,13,6], (28,9): [28,13,32,24], (28,10): [32,2],
    (28,11): [6,28,32], (28,12): [6,28,32], (28,13): [32,35,13],
    (28,14): [28,6,32], (28,15): [28,6,32], (28,18): [10,26,24],
    (28,19): [6,19,28,24], (28,20): [6,1,32], (28,22): [3,6,32],
    (28,24): [3,6,32], (28,25): [26,32,27], (28,26): [10,16,31,28],
    (28,29): [24,34,28,32], (28,30): [2,6,32], (28,31): [5,11,1,23],
    (28,32): [28,24,22,26], (28,33): [3,33,39,10], (28,34): [6,35,25,18],
    (28,35): [1,13,17,34], (28,36): [1,32,13,11], (28,37): [13,35,2],
    (28,38): [27,35,10,34], (28,39): [26,24,32,28],
    # Row 29
    (29,1): [28,32,13,18], (29,2): [28,35,27,9], (29,3): [10,28,29,37],
    (29,4): [2,32,10], (29,5): [28,33,29,32], (29,6): [2,29,18,36],
    (29,7): [32,23,2], (29,8): [25,10,35], (29,9): [10,28,32],
    (29,10): [28,19,34,36], (29,11): [3,35], (29,12): [32,30,40],
    (29,13): [30,18], (29,14): [3,27], (29,15): [3,27,40],
    (29,17): [19,26], (29,18): [3,32], (29,19): [32,2],
    (29,21): [13,32,2], (29,22): [35,31,10,24], (29,24): [32,26,28,18],
    (29,25): [32,30], (29,26): [11,32,1], (29,28): [26,28,10,36],
    (29,30): [4,17,34,26], (29,32): [1,32,35,23], (29,33): [25,10],
    (29,34): [26,2,18], (29,36): [26,28,18,23], (29,37): [10,18,32,39],
    (29,38): [35,31,10,24], (29,39): [35,26,27,10],
    # Row 30
    (30,1): [22,21,27,39], (30,2): [2,22,13,24], (30,3): [17,1,39,4],
    (30,4): [1,18], (30,5): [22,1,33,28], (30,6): [27,2,39,35],
    (30,7): [22,23,37,35], (30,8): [34,39,19,27], (30,9): [21,22,35,28],
    (30,10): [13,35,39,18], (30,11): [22,2,37], (30,12): [22,1,3,35],
    (30,13): [35,24,30,18], (30,14): [18,35,37,1], (30,15): [22,15,33,28],
    (30,16): [17,1,40,33], (30,17): [22,33,35,2], (30,18): [1,19,32,13],
    (30,19): [1,24,6,27], (30,20): [10,2,22,37], (30,21): [19,22,31,2],
    (30,22): [21,22,35,2], (30,23): [33,22,19,40], (30,24): [22,10,2],
    (30,25): [35,18,34], (30,26): [35,33,29,31], (30,27): [27,24,2,40],
    (30,28): [28,33,23,26], (30,29): [26,28,10,18], (30,31): [24,35,2],
    (30,32): [2,25,28,39], (30,33): [35,10,2], (30,34): [35,11,22,31],
    (30,35): [22,19,29,40], (30,36): [22,19,29,40], (30,37): [33,3,34],
    (30,38): [22,35,13,24], (30,39): [22,35,13,24],
    # Row 31
    (31,1): [19,22,15,39], (31,2): [35,22,1,39], (31,3): [17,15,16,22],
    (31,5): [17,2,18,39], (31,6): [22,1,40], (31,7): [17,2,40],
    (31,8): [30,18,35,4], (31,9): [35,28,3,23], (31,10): [35,28,1,40],
    (31,11): [2,33,27,18], (31,12): [35,1], (31,13): [35,40,27,39],
    (31,14): [15,35,22,2], (31,15): [15,22,33,31], (31,16): [21,39,16,22],
    (31,17): [22,35,2,24], (31,18): [19,24,39,32], (31,19): [2,35,6],
    (31,20): [19,22,18], (31,21): [2,35,18], (31,22): [21,35,2,22],
    (31,23): [10,1,34], (31,24): [10,21,29], (31,25): [1,22],
    (31,26): [3,24,39,1], (31,27): [24,2,40,39], (31,28): [3,33,26],
    (31,29): [4,17,34,26], (31,32): [1,35,12,18], (31,34): [24,2],
    (31,39): [19,1,31],
    # Row 32
    (32,1): [28,29,15,16], (32,2): [1,27,36,13], (32,3): [1,29,13,17],
    (32,4): [15,17,27], (32,5): [13,1,26,12], (32,6): [16,40],
    (32,7): [13,29,1,40], (32,8): [35], (32,9): [35,13,8,1],
    (32,10): [35,12], (32,11): [35,19,1,37], (32,12): [1,28,13,27],
    (32,13): [11,13,1], (32,14): [1,3,10,32], (32,15): [27,1,4],
    (32,16): [35,16], (32,17): [27,26,18], (32,18): [28,24,27,1],
    (32,19): [28,26,27,1], (32,20): [1,4], (32,21): [27,1,12,24],
    (32,22): [19,35], (32,23): [15,34,33], (32,24): [32,24,18,16],
    (32,25): [35,28,34,4], (32,26): [35,23,1,24], (32,28): [1,35,12,18],
    (32,30): [24,2], (32,33): [2,5,13,16], (32,34): [35,1,11,9],
    (32,35): [2,13,15], (32,36): [27,26,1], (32,37): [6,28,11,1],
    (32,38): [8,28,1], (32,39): [35,1,10,28],
    # Row 33
    (33,1): [25,2,13,15], (33,2): [6,13,1,25], (33,3): [1,17,13,12],
    (33,5): [1,17,13,16], (33,6): [18,16,15,39], (33,7): [1,16,35,15],
    (33,8): [4,18,39,31], (33,9): [18,13,34], (33,10): [28,13,35],
    (33,11): [2,32,12], (33,12): [15,34,29,28], (33,13): [32,35,30],
    (33,14): [32,40,3,28], (33,15): [29,3,8,25], (33,16): [1,16,25],
    (33,17): [26,27,13], (33,18): [13,17,1,24], (33,19): [1,13,24],
    (33,21): [35,34,2,10], (33,22): [2,19,13], (33,23): [28,32,2,24],
    (33,24): [4,10,27,22], (33,25): [4,28,10,34], (33,26): [12,35],
    (33,27): [17,27,8,40], (33,28): [25,13,2,34], (33,29): [1,32,35,23],
    (33,30): [2,25,28,39], (33,32): [2,5,12], (33,34): [12,26,1,32],
    (33,35): [15,34,1,16], (33,36): [32,26,12,17], (33,38): [1,34,12,3],
    (33,39): [15,1,28],
    # Row 34
    (34,1): [2,27,35,11], (34,2): [2,27,35,11], (34,3): [1,28,10,25],
    (34,4): [3,18,31], (34,5): [15,13,32], (34,6): [16,25],
    (34,7): [25,2,35,11], (34,8): [1], (34,9): [34,9],
    (34,10): [1,11,10], (34,11): [13], (34,12): [1,13,2,4],
    (34,13): [2,35], (34,14): [11,1,2,9], (34,15): [11,29,28,27],
    (34,16): [1], (34,17): [4,10], (34,18): [15,1,13],
    (34,19): [15,1,28,16], (34,21): [15,10,32,2], (34,22): [15,1,32,19],
    (34,23): [2,35,34,27], (34,25): [32,1,10,25], (34,26): [2,28,10,25],
    (34,27): [11,10,1,16], (34,28): [10,2,13], (34,29): [25,10],
    (34,30): [35,10,2,16], (34,32): [1,35,11,10], (34,33): [1,12,26,15],
    (34,35): [7,1,4,16], (34,36): [35,1,13,11], (34,38): [34,35,7,13],
    (34,39): [1,32,10],
    # Row 35
    (35,1): [1,6,15,8], (35,2): [19,15,29,16], (35,3): [35,1,29,2],
    (35,4): [1,35,16], (35,5): [35,30,29,7], (35,6): [15,16],
    (35,7): [15,35,29], (35,9): [35,10,14], (35,10): [15,17,20],
    (35,11): [35,16], (35,12): [15,37,1,8], (35,13): [35,30,14],
    (35,14): [35,3,32,6], (35,15): [13,1,35], (35,16): [2,16],
    (35,17): [27,2,3,35], (35,18): [6,22,26,1], (35,19): [19,35,29,13],
    (35,21): [19,1,29], (35,22): [18,15,1], (35,23): [15,10,2,13],
    (35,25): [35,28], (35,26): [3,35,15], (35,27): [35,13,8,24],
    (35,28): [35,5,1,10], (35,30): [35,11,32,31], (35,32): [1,13,31],
    (35,33): [15,34,1,16], (35,34): [1,16,7,4], (35,36): [15,29,37,28],
    (35,37): [1], (35,38): [27,34,35], (35,39): [35,28,6,37],
    # Row 36
    (36,1): [26,30,34,36], (36,2): [2,26,35,39], (36,3): [1,19,26,24],
    (36,4): [26], (36,5): [14,1,13,16], (36,6): [6,36],
    (36,7): [34,26,6], (36,8): [1,16], (36,9): [34,10,28],
    (36,10): [26,16], (36,11): [19,1,35], (36,12): [29,13,28,15],
    (36,13): [2,22,17,19], (36,14): [2,13,28], (36,15): [10,4,28,15],
    (36,17): [2,17,13], (36,18): [24,17,13], (36,19): [27,2,29,28],
    (36,21): [20,19,30,34], (36,22): [10,35,13,2], (36,23): [35,10,28,29],
    (36,25): [6,29], (36,26): [13,3,27,10], (36,27): [13,35,1],
    (36,28): [2,26,10,34], (36,29): [26,24,32], (36,30): [22,19,29,40],
    (36,31): [19,1], (36,32): [27,26,1,13], (36,33): [27,9,26,24],
    (36,34): [1,13], (36,35): [29,15,28,37], (36,37): [15,10,37,28],
    (36,38): [15,1,24], (36,39): [12,17,28],
    # Row 37
    (37,1): [27,26,28,13], (37,2): [6,13,28,1], (37,3): [16,17,26,24],
    (37,4): [26], (37,5): [2,13,18,17], (37,6): [2,39,30,16],
    (37,7): [29,1,4,16], (37,8): [2,18,26,31], (37,9): [3,4,16,35],
    (37,10): [30,28,40,19], (37,11): [35,36,37,32], (37,12): [27,13,1,39],
    (37,13): [11,22,39,30], (37,14): [27,3,15,28], (37,15): [19,29,39,25],
    (37,16): [25,34,6,35], (37,17): [3,27,35,16], (37,18): [2,24,26],
    (37,19): [35,38], (37,20): [19,35,16], (37,21): [18,1,16,10],
    (37,22): [35,3,15,19], (37,23): [1,18,10,24], (37,24): [35,33,27,22],
    (37,25): [18,28,32,9], (37,26): [3,27,29,18], (37,27): [27,40,28,8],
    (37,28): [26,24,32,28], (37,30): [22,19,29,28], (37,31): [2,21],
    (37,32): [5,28,11,29], (37,33): [2,5], (37,34): [12,26],
    (37,35): [1,15], (37,36): [15,10,37,28], (37,38): [34,21],
    (37,39): [35,18],
    # Row 38
    (38,1): [28,26,18,35], (38,2): [28,26,35,10], (38,3): [14,13,17,28],
    (38,4): [23], (38,5): [17,14,13], (38,7): [35,13,16],
    (38,9): [28,10], (38,10): [2,35], (38,11): [13,35],
    (38,12): [15,32,1,13], (38,13): [18,1], (38,14): [25,13],
    (38,15): [6,9], (38,17): [26,2,19], (38,18): [8,32,19],
    (38,19): [2,32,13], (38,21): [28,2,27], (38,22): [23,28],
    (38,23): [35,10,18,5], (38,24): [35,33], (38,25): [24,28,35,30],
    (38,26): [35,13], (38,27): [11,27,32], (38,28): [28,26,10,34],
    (38,29): [28,26,18,23], (38,30): [2,33], (38,31): [2],
    (38,32): [1,26,13], (38,33): [1,12,34,3], (38,34): [1,35,13],
    (38,35): [27,4,1,35], (38,36): [15,24,10], (38,37): [34,27,25],
    (38,39): [5,12,35,26],
    # Row 39
    (39,1): [35,26,24,37], (39,2): [28,27,15,3], (39,3): [18,4,28,38],
    (39,4): [30,7,14,26], (39,5): [10,26,34,31], (39,6): [10,35,17,7],
    (39,7): [2,6,34,10], (39,8): [35,37,10,2], (39,10): [28,15,10,36],
    (39,11): [10,37,14], (39,12): [14,10,34,40], (39,13): [35,3,22,39],
    (39,14): [29,28,10,18], (39,15): [35,10,2,18], (39,16): [20,10,16,38],
    (39,17): [35,21,28,10], (39,18): [26,17,19,1], (39,19): [35,10,38,19],
    (39,20): [1], (39,21): [35,20,10], (39,22): [28,10,29,35],
    (39,23): [28,10,35,23], (39,24): [13,15,23], (39,26): [35,38],
    (39,27): [1,35,10,38], (39,28): [1,10,34,28], (39,29): [18,10,32,1],
    (39,30): [22,35,13,24], (39,31): [35,22,18,39], (39,32): [35,28,2,24],
    (39,33): [1,28,7,10], (39,34): [1,32,10,25], (39,35): [1,35,28,37],
    (39,36): [12,17,28,24], (39,37): [35,18,27,2], (39,38): [5,12,35,26],
}


def build_matrix_dict(raw):
    """Convert (i,j)->[principles] dict to nested string-keyed dict."""
    matrix = {}
    for (i, j), principles in raw.items():
        si, sj = str(i), str(j)
        if si not in matrix:
            matrix[si] = {}
        matrix[si][sj] = principles
    return matrix


def build_altshuller_39x39():
    data = {
        "meta": {
            "name": "Classic Altshuller TRIZ Contradiction Matrix",
            "version": "Original (1971-1985)",
            "author": "Genrich Altshuller",
            "year": "1971",
            "domain": "General engineering",
            "dimensions": "39x39",
            "source_url": "https://www.triz40.com/aff_Matrix_TRIZ.php",
            "license": "Public domain",
            "notes": "Classic 39-parameter, 40-principle contradiction matrix. Parameters and principles extracted from triz40.com."
        },
        "parameters": PARAMETERS,
        "principles": PRINCIPLES,
        "matrix": build_matrix_dict(MATRIX_RAW)
    }
    return save_json("altshuller_39x39.json", data)


# ============================================================
# BioTRIZ 6x6 matrix
# ============================================================
def build_biotriz_6x6():
    bio_params = {
        "1": {"name": "Substance", "description": "Hierarchically structured material"},
        "2": {"name": "Structure", "description": "Material composition and organization"},
        "3": {"name": "Space", "description": "Spatial arrangement and dimensions"},
        "4": {"name": "Time", "description": "Temporal dynamics and sequences"},
        "5": {"name": "Energy", "description": "Power requirements and regulation"},
        "6": {"name": "Information", "description": "Data, signals, and control mechanisms"},
    }

    # Technology matrix (from PRIZM paper)
    matrix_tech = {
        "1": {"1": [6,10,26,27,31,40], "2": [27], "3": [14,15,29,40], "4": [3,27,38], "5": [10,12,18,19,31], "6": [3,15,22,27,29]},
        "2": {"1": [15], "2": [18,26], "3": [1,13], "4": [27,28], "5": [19,36], "6": [1,23,24]},
        "3": {"1": [8,14,15,29,39,40], "2": [1,30], "3": [4,5,7,8,9,14,17], "4": [4,14], "5": [6,8,15,36,37], "6": [1,15,16,17,30]},
        "4": {"1": [3,38], "2": [4,28], "3": [5,14,30,34], "4": [10,20,38], "5": [19,35,36,38], "6": [22,24,28,34]},
        "5": {"1": [8,9,18,19,31,36,37,38], "2": [32], "3": [12,15,19,30,36,37,38], "4": [6,19,35,36,37], "5": [14,19,21,25,36,37,38], "6": [2,19,22]},
        "6": {"1": [3,11,22,25,28,35], "2": [30], "3": [1,4,16,17,39], "4": [9,22,25,28,34], "5": [2,6,19,22,32], "6": [2,11,12,21,22,23,27,33,34]},
    }

    # Biology matrix (from PRIZM paper)
    matrix_bio = {
        "1": {"1": [13,15,17,20,31,40], "2": [1,2,3,15,24,26], "3": [1,5,13,15,31], "4": [15,19,27,29,30], "5": [3,6,9,25,31,35], "6": [3,25,26]},
        "2": {"1": [1,10,15,19], "2": [1,15,19,24,34], "3": [10], "4": [1,2,4], "5": [1,2,4], "6": [1,3,4,15,19,24,25,35]},
        "3": {"1": [3,14,15,25], "2": [2,3,4,5,10,15,19], "3": [4,5,14,17,36], "4": [1,19,29], "5": [1,3,4,15,19], "6": [3,15,21,24]},
        "4": {"1": [1,3,15,20,25,38], "2": [1,2,3,4,6,15,17,19], "3": [1,2,3,4,7,38], "4": [2,3,11,20,26], "5": [3,9,15,20,22,25], "6": [1,2,3,10,19,23]},
        "5": {"1": [1,3,13,14,17,25,31], "2": [1,3,5,6,25,35,36,40], "3": [1,3,4,15,25], "4": [3,10,23,25,35], "5": [3,5,9,22,25,32,37], "6": [1,3,4,15,16,25]},
        "6": {"1": [1,6,22], "2": [1,3,6,18,22,24,32,34,40], "3": [3,20,22,25,33], "4": [2,3,9,17,22], "5": [1,3,6,22,32], "6": [3,10,16,23,25]},
    }

    # Use standard TRIZ principles (subset that are referenced)
    all_referenced = set()
    for m in [matrix_tech, matrix_bio]:
        for row in m.values():
            for cell in row.values():
                all_referenced.update(str(p) for p in cell)

    bio_principles = {k: v for k, v in PRINCIPLES.items() if k in all_referenced}

    data = {
        "meta": {
            "name": "BioTRIZ / PRIZM Contradiction Matrix",
            "version": "2006",
            "author": "Julian Vincent, Darrell Mann, Olga Bogatyreva",
            "year": "2006",
            "domain": "Biology vs Technology problem solving",
            "dimensions": "6x6",
            "source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1664643/",
            "license": "Creative Commons (PMC Open Access)",
            "notes": "Contains two matrices: technology-derived (PRIZM) and biology-derived. The 6 parameters are operational fields. Overall similarity between biology and technology solutions is 12%. Diagonal cells are included as they represent same-field contradictions."
        },
        "parameters": bio_params,
        "principles": bio_principles,
        "matrix_technology": matrix_tech,
        "matrix_biology": matrix_bio,
    }
    return save_json("biotriz_6x6.json", data)


# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    print("Building TRIZ matrix JSON files...\n")
    build_altshuller_39x39()
    build_biotriz_6x6()
    print("\nDone!")
