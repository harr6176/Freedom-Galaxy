#from database_creation import loadDatabase
from orm import *
from random import randint
 
#Start Character Combat
#Authored By Jeff Crocker
def char_combat(session, atk_id, def_id, options):

    atk_stack = session.query(Stack).filter_by(id = atk_id).one()
    def_stack = session.query(Stack).filter_by(id = def_id).one()
    session.add(atk_stack, def_stack)

    # still needs to include breakoff


    CD = char_combat_rating(atk_stack, session) - char_combat_rating(def_stack, session)

    if 'C' in options:
        CD -= 2

    atk_result = char_table(randint(0,5),CD,True)
    def_result = char_table(randint(0,5),CD,False)

    if 'F' in options:
        atk_result[0] *= 2
        def_result[0] *= 2

    if atk_stack.units:
        atk_result[0] *= 2
        def_result[0] *= 2

    char_wounds(atk_stack, atk_result[0], session)
    char_wounds(def_stack, def_result[0], session)
'''        
    if 'C' in options:
        if atk_result[1] == 1:
            captured_char = def_stack.characters[randint(0,len(def_stack.characters)-1)]
            captured_char.stack_id = atk_id
            captured_char.captive = True
            captured_char.active = False

        if def_result[1] == 1:
            captured_char = def_stack.characters[randint(0,len(def_stack.characters)-1)]
            captured_char.stack_id = atk_id
            captured_char.captive = True
            captured_char.active = False
'''
    if atk_stack.size() == 0:
        session.delete(atk_stack)

    if def_stack.size() == 0:
        session.delete(def_stack)

    return True, atk_stack.__dict__, def_stack.__dict__

def char_combat_rating(StackID, session):
    CR = 0
    # for each character in the stack, sum effective combat strength
    for character in session.query(Stack).filter_by(id = StackID).one().characters:
        if character.active == True:
            CR += character.combat - character.wounds
    return CR

def char_wounds(stack, num_wounds, session):
    # while there are still wounds to assign and characters alive
    while num_wounds > 0 and stack.characters:
        # select random victim from stack
        victim = stack.characters[randint(0,len(stack.characters)-1)]
        session.add(victim)
        victim.wounds += 1
        #print victim.name, " suffers wound!"
        if victim.wounds >= victim.endurance:
            #print victim.name, " has died! :("
            session.delete(victim)
        num_wounds -= 1

    session.commit()

# Simply a direct transfer of character combat table
def char_table(dice, CD, is_attacker):
    attacker_wounds = (
        (4,3,3,2,2,2,2,1,1,1),(4,3,2,2,2,1,1,1,1,0),(3,3,2,2,1,1,1,1,0,0),
        (3,2,2,1,1,1,0,0,0,0),(2,2,1,1,0,0,0,0,0,0),(2,1,0,0,0,0,0,0,0,0))

    defender_wounds = (
        (0,0,0,0,0,0,0,1,1,2),(0,0,0,0,0,0,1,1,1,2),(0,0,0,0,0,1,1,1,2,3),
        (0,0,0,1,1,1,1,2,3,3),(0,0,1,1,1,1,2,2,3,4),(1,1,1,1,2,2,2,3,3,4))

    attacker_capture = (
        (0,0,0,0,0,1,0,0,0,0),(0,0,0,1,1,0,1,1,1,0),(0,1,0,0,0,0,0,0,0,0),
        (0,0,1,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,1,0,0),(0,0,0,0,0,0,0,0,0,0))

    defender_capture = (
        (0,0,0,0,0,0,0,0,1,0),(0,0,0,0,0,0,0,0,0,0),(0,0,0,0,1,0,0,1,1,0),
        (0,0,0,1,0,1,1,1,0,0),(0,0,0,0,0,0,1,0,1,0),(0,0,0,0,0,0,0,0,0,0))

    # A ridiculous way of translating Combat Differentials to appropriate columns
    if CD <= -7:
        CD = 0
    elif CD >= -6 and CD <= -4:
        CD = 1
    elif CD >= -3 and CD <= -2:
        CD = 2
    elif CD == -1:
        CD = 3
    elif CD == 0:
        CD = 4
    elif CD == 1:
        CD = 5
    elif CD >= 2 and CD <= 3:
        CD = 6
    elif CD >= 4 and CD <= 6:
        CD = 7
    elif CD >= 7 and CD <= 10:
        CD = 8
    elif CD >= 11:
        CD = 9

    if is_attacker:
        return (attacker_wounds[dice][CD], attacker_capture[dice][CD])
    else:
        return (defender_wounds[dice][CD], defender_capture[dice][CD])
#End Character Combat

#Start Military Combat
#Authored By Ben Cumber
def mil_combat(session, atk_id, def_id):

    atk_stack = session.query(Stack).filter_by(id = atk_id).one()
    def_stack = session.query(Stack).filter_by(id = def_id).one()

    #atk_mil_units = atk_stack.units
    #def_mil_units = def_stack.units
    atk_combat_rating = stack_combat_rating(atk_stack)
    def_combat_rating = stack_combat_rating(def_stack)
    
    #print "Attacker Combat Rating: ", atk_combat_rating
    #print "Defender Combat Rating: ", def_combat_rating

    column = stack_combat_ratio(atk_combat_rating, def_combat_rating)
    column += mil_combat_modifiers(atk_stack, def_stack)

    #print "Column: ", column

    if(column > 10):
        column = 10
    if(column < 0):
        column = 0

    atk_result = mil_combat_table(randint(0,5), column, True)
    def_result = mil_combat_table(randint(0,5), column, False)

    apply_result(atk_result, atk_stack)
    apply_result(def_result, def_stack)
    #print "Attackers Eliminated: ", atk_result
    #print "Defenders Eliminated: ", def_result

    #atk_result = mil_combat_table(randint(0, 5), combat_ratio, True)
    #def_result = mil_combat_table(randint(0, 5), combat_ratio, False)

    return True, atk_stack.__dict__, def_stack.__dict__

def apply_result(dmg, stack_obj):
    unit_list = list()
    if (stack_obj.location_id % 10 == 0):           #if true, space combat.
        for unit in stack_obj.units:
            if(unit.space_combat < dmg):
                dmg = dmg - unit.space_combat
                #session.add(unit)
                session.delete(unit)
    else:                                           #otherwise, environ combat
        for militaryunit in stack_obj.units:
            if(unit.environ_combat < dmg):
                dmg = dmg - unit.environ_combat
                #session.add(unit)
                session.delete(unit)

    session.commit
def stack_combat_ratio(atk_rating, def_rating):     #Always round in the
    ratio = 0                                       #defenders favor
    column = 1
    #columns 0 and 10 are only accessible through a modifier shift.

    if(atk_rating > def_rating):#columns 6-9
        ratio =  atk_rating / def_rating
        if(ratio == 1):
            column = 5
        elif(ratio == 2):
            column = 6
        elif(ratio == 3):
            column = 7
        elif(ratio == 4):
            column = 8
        else:
            column = 9
    elif(atk_rating < def_rating):#columns 1-4
        ratio = def_rating / atk_rating
        ratio += 1
        if(ratio >= 5):
            column = 1
        elif(ratio == 4):
            column = 2
        elif(ratio == 3):
            column = 3
        else:
            column = 4
    else:
        #they are equal, the ratio is 1:1, column 5
        column = 5
    return column

def mil_combat_modifiers(atk_obj, def_obj):
    modifier = 0
    atk_leader = atk_obj.find_stack_leader()
    def_leader = def_obj.find_stack_leader()
    leadership = abs(atk_leader - def_leader)
    if(atk_leader > def_leader):
        modifier += leadership
    elif(def_leader > atk_leader):
        modifier -= leadership
    #leadership modifier done

    #now for Rebel unit environ type modifier
    #Step 1:
        #Determine which stack is rebel.
    #Step 2:
        #Determine what type of environ, combat is occuring in.
    #Step 3:
        #Check if rebel units are of same environ type.
    #Step 4:
        #if yes: Shift in their favor.
        #if no: do nothing

#trouble referencing the environ that the stack is in.
#    if atk_obj.is_rebel_stack():
#        if atk_obj.check_rebel_environ():
#            modifier += 1
#    else:
#        if def_obj.check_rebel_environ():
#            modifier -= 1

    #now for special environ modifier (Rebels favor only)
    #occurs only if combat is in liquid, subterranean, air, or fire environ.
    #and only if there is not an imperial leader present.
    #Step 1:
        #Is it a special environ?
    #Step 2:
        #Do the imperials have a leader?
    #Step 3:
        #If 1 is true and 2 is false shift 1 in rebels favor.
        #Else, Do nothing.
    return modifier

def stack_combat_rating(stack_obj):
    combat_rating = 0

    if (stack_obj.location_id % 10 == 0):           #if true, space combat.
        for militaryunit in stack_obj.units:
            combat_rating += militaryunit.space_combat
    else:                                           #otherwise, environ combat
        for militaryunit in stack_obj.units:
            combat_rating += militaryunit.environ_combat

    return combat_rating

def mil_combat_table(die_roll, combat_odds, is_attacker):
    attacker_wounds = (
            (8, 7, 6, 5, 5, 4, 3, 3, 2, 2, 1),
            (7, 6, 5, 5, 4, 3, 2, 2, 1, 1, 1),
            (7, 5, 5, 4, 3, 2, 2, 2, 1, 1, 1),
            (6, 5, 4, 3, 3, 2, 1, 1, 1, 0, 0),
            (5, 4, 4, 3, 2, 1, 1, 0, 0, 0, 0),
            (4, 4, 3, 3, 1, 0, 0, 0, 0, 0, 0))

    defender_wounds = (
            (0, 0, 0, 0, 0, 0, 1, 2, 2, 3, 4),
            (0, 0, 0, 0, 0, 1, 2, 3, 3, 4, 5),
            (0, 0, 0, 0, 1, 1, 2, 3, 4, 4, 5),
            (0, 0, 1, 1, 1, 2, 3, 3, 4, 5, 6),
            (1, 1, 1, 1, 2, 2, 3, 4, 5, 6, 7),
            (1, 1, 1, 2, 2, 3, 4, 5, 6, 7, 8))
    #print "Die Roll", die_roll+1
    if is_attacker:
        return (attacker_wounds[die_roll][combat_odds])
    else:
        return (defender_wounds[die_roll][combat_odds])
#end Military Combat

#start Search
#Authored by Ben Cumber
def search(session, atk_obj, def_obj):
    if(atk.obj.characters):
        if(atk_obj.units):
            #characters and military units
            leadership_rating = atk_obj.find_stack_leader()
            for unit in atk_obj.units:
                military_rating += unit.environ_combat
            search_value = leadership_rating + military_rating
        else:
            #characters only
            for character in atk_obj.characters:
                search_value += character.intelligence
                character.detected = True
    else:
        #military units only
        for unit in atk_obj.units:
            search_value += unit.environ_combat

    if(search_value == 1):
        search_value = 0
    elif(search_value == 2 or search_value == 3):
        search_value = 1
    elif(search_value > 3 and search_value < 7):
        search_value = 2
    elif(search_value > 6 and search_value < 10):
        search_value = 3
    elif(search_value > 9 and search_value < 14):
        search_value = 4
    elif(search_value > 13 and search_value < 18):
        search_value = 5
    elif(search_value > 17 and search_value < 23):
        search_value = 6
    else:
        search_value = 7

    hiding_value = 0
    num_chars = 0
    for character in def_obj.characters:
        num_chars += 1
        if(character.intelligence > hiding_value):
            hiding_value = character.intelligence
    hiding_value += def_obj.environ.size
    hiding_value -= num_chars

    if(hiding_value <= 1):
        hiding_value = 0
    elif(hiding_value == 2 or hiding_value == 3):
        hiding_value = 1
    elif(hiding_value == 4 or hiding_value == 5):
        hiding_value = 2
    elif(hiding_value == 6 or hiding_value == 7):
        hiding_value = 3
    else:
        hiding_value = 4

    result = search_table(search_value, hiding_value)

    if(result == 6):
        #characters are found, combat will result.
        if(atk_obj.units):
            return squad_combat(session, atk_obj, def_obj.id)
        else:
            return char_combat(session, atk_obj.id, def_obj.id)
    elif(result == 0):
        #characters are not found, nothing happens
        pass
    else:
        if(randint(0,5) <= result):
            #characters are found, combat results
            if(atk_obj.units):
                return squad_combat(session, atk_obj, def_obj.id)
            else:
                return char_combat(session, atk_obj.id, def_obj.id)

def squad_combat(session, atk_obj, def_id):
    for unit in atk_obj.units:
        strength += unit.environ_combat
    if(strength == 1):
        strength = 0
    elif(strength == 2):
        strength = 1
    elif(strength == 3 or strength == 4):
        strength = 2
    elif(strength > 4 and strength < 8):
        strength = 3
    elif(strength > 7 and strength < 12):
        strength = 4
    else:
        strength = 5

    attributes = squad_table(strength)
    
    if(atk_obj.characters):
        if(atk_obj.units):
            attributes[1] += 2
    squad = Character("squad", None, None, None, atk_obj.side(), 
                attributes[0], attributes[1], 0, 0, 0, 
                0, None, None) 
    new_stack = Stack()
    session.add(new_stack)
    new_stack.characters.append(squad)
    session.commit
    new_id = session.query(Character).filter_by(name = "squad").one().stack_id
    result = char_combat(session, new_id, def_id, None)
    session.delete(squad, new_stack)
    session.commit()
    return result

def squad_table(strength):
    squad_result = (
            (4, 4)
            (6, 4)
            (8, 6)
            (10, 6)
            (12, 8)
            (14, 8))
    return squad_result[strength]

def search_table(search_value, hiding_value):
    search_results = (
            (1, 2, 3, 4, 4, 5, 6, 6)
            (1, 1, 2, 3, 4, 4, 5, 6)
            (0, 1, 1, 2, 3, 4, 4, 5)
            (0, 0, 1, 1, 2, 2, 3, 4)
            (0, 0, 0, 1, 1, 1, 2, 3))

    return search_results(hiding_value, search_value)
