import re, json, os, sys
import wikitextparser as wtp
import fnmatch

def remove_consecutive_linebreaks(text):
  return re.sub(r'\n\n+', '\n\n', text)

def find_file(name, path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if fnmatch.fnmatchcase(file, name):
                return os.path.join(root, file)

    for dir in dirs:
        found = find_file(name, os.path.join(root, dir))
        if found:
            return found

def format_abilities(str):
    parsed = wtp.parse(str)
    abilities = []
    for template in parsed.templates:
        if template.name.lower() == 'melee':
            abilities.append(format_melee(template))
        elif template.name.lower() == 'ability':
            abilities.append(format_ability(template))
        elif template.name.lower() == 'healing':
            abilities.append(format_healing(template))
    return abilities

def format_melee(template):
    min = '0'
    max = '0'
    for arguments in template.arguments:
        if arguments.name.lower() == '1':
            try:
                if '-' in arguments.value:
                    min, max = arguments.value.split('-')
                else:
                    min = arguments.value
                    max = arguments.value
            except:
                min = arguments.value
                max = arguments.value
    return {
            'type': 'melee',
            'min': min,
            'max': max
    }

def format_ability(template):
    name = 'unknown'
    min = '0'
    max = '0'
    element = 'unknown'
    for arguments in template.arguments:
        if arguments.name.lower() == '1':
            name = arguments.value
        elif arguments.name.lower() == '2':
            try:
                if '-' in arguments.value:
                    min, max = arguments.value.split('-')
                else:
                    min = arguments.value
                    max = arguments.value
            except:
                min = arguments.value
                max = arguments.value
        elif arguments.name.lower() == 'element':
            element = arguments.value
    return {
        'type': 'ability',
        'name': name,
        'min': min,
        'max': max,
        'element': element.strip().lower() if element else None
    }

def format_healing(template):
    min = "0"
    max = "0"
    for arguments in template.arguments:
        if arguments.name.lower() == 'range':
            try:
                if '-' in arguments.value:
                    min, max = arguments.value.split('-')
                elif '~' in arguments.value:
                    val = int(arguments.value.replace('~', ''))
                    min, max = str(int(val*0.75)), str(val)
                else:
                    min = arguments.value
                    max = arguments.value
            except:
                min = arguments.value
                max = arguments.value
    return {
        'type': 'healing',
        'min': min,
        'max': max
    }

def abilities_as_lua(abilities):
    lua = '-- TODO: monster-abilities\n'
    lua += '--monster.attacks = {\n'
    for ability in abilities:
        if ability['type'] == 'melee':
            lua += format_melee_lua(ability)
        elif ability['type'] == 'ability':
            lua += format_ability_lua(ability)
        elif ability['type'] == 'healing':
            lua += format_healing_lua(ability)
    lua += '--}'
    return lua

def format_melee_lua(ability):
    return '--\t{name ="melee", interval = 2000, chance = 100, minDamage = -' + ability['min'] + ', maxDamage = -' + ability['max'] + '},\n'

def format_element(element):
  if element == 'physical':
      return 'COMBAT_PHYSICALDAMAGE'
  elif element == 'energy':
      return 'COMBAT_ENERGYDAMAGE'
  elif element == 'earth':
      return 'COMBAT_EARTHDAMAGE'
  elif element == 'fire':
      return 'COMBAT_FIREDAMAGE'
  elif element == 'ice':
      return 'COMBAT_ICEDAMAGE'
  elif element == 'holy':
      return 'COMBAT_HOLYDAMAGE'
  elif element == 'death':
      return 'COMBAT_DEATHDAMAGE'
  elif element == 'lifedrain':
      return 'COMBAT_LIFEDRAIN'
  elif element == 'manadrain':
      return 'COMBAT_MANADRAIN'
  else:
      return 'COMBAT_PHYSICALDAMAGE'

def format_ability_lua(ability):
    return '--\t{name ="combat", interval = 2000, chance = 20, type = ' + format_element(ability['element']) + ', minDamage = -' + ability['min'] + ', maxDamage = -' + ability['max'] + ', range = ?, effect = <>, target = ?}, --' + ability['name'] + '\n'

def format_healing_lua(ability):
    return '--\t{name ="healing", interval = 2000, chance = 20, minDamage = ' + ability['min'] + ', maxDamage = ' + ability['max'] + '},\n'

if(len(sys.argv) < 2):
    print("Usage: python creature_lua_gen.py <canary monster directory>")
    sys.exit()

creatureName = ''
if(len(sys.argv) >= 3):
    creatureName = sys.argv[2]
else:
    creatureName = input('enter creature name: ')

jsonFileName = creatureName
jsonFileName = jsonFileName.replace(' ', '_') + ".json"
luaFileName = creatureName.lower()
luaFileName = luaFileName.replace(' ', '_').replace('_(creature)', '').replace("'", "")
luaFileName = luaFileName + '.lua'

# url = 'https://raw.githubusercontent.com/luan/tibiawiki/main/data/' + str(jsonFileName) + '.json'
# resp = requests.get(url)

dir_path = os.path.dirname(os.path.realpath(__file__))
data = None
jsonLoc = find_file(jsonFileName, os.path.join(dir_path, 'data'))

if not jsonLoc:
    sys.exit()

with open(jsonLoc) as f:
    data = json.load(f)

fileLoc = sys.argv[1]
monsterLoc =  find_file(luaFileName, os.path.join(dir_path, fileLoc))
if not monsterLoc:
    print(creatureName)
    sys.exit()

isBoss = data.setdefault('isboss', 'no') == 'yes'

### VARIABLES
variables = 'local mType = Game.createMonsterType("' + str(data['name']) + '")\n'
variables += 'local monster = {}\n'


### DESCRIPTION
description = 'monster.description = "'
actualName = data.setdefault('actualname', data['name'])
actualNameFirstLetter = actualName[0]

if not isBoss:
    if (actualNameFirstLetter == 'a' or actualNameFirstLetter == 'e' or actualNameFirstLetter == 'i' or actualNameFirstLetter == 'o' or actualNameFirstLetter == 'u'):
        description += 'an '
    else:
        description += 'a '
description += actualName + '"\n'

### EXPERIENCE
if ('exp' in data):
    experience = 'monster.experience = ' + str(data['exp']) + '\n'
else:
    experience = 'monster.experience = 0\n'


### OUTFIT
outfit = ''
with open(monsterLoc) as file:
    copying = False
    braces = 0
    for line in file:
        lineStr = line.rstrip()
        if (copying):
            braces += lineStr.count('{')
            braces -= lineStr.count('}')
            if (braces < 1):
                copying = False
                break
            outfit += lineStr + '\n'
        if (lineStr.startswith("monster.outfit = ")):
            braces += 1
            copying = True
            outfit += lineStr + '\n'

outfit += '}\n'

bosstiary = ''
raceid = ''
beastiary = ''

if isBoss:
    if 'race_id' in data:
        ### BOSSTIARY
        bossid = data['race_id']
        rarity = 'RARITY_' + data.setdefault('bosstiaryclass', 'Archfoe').upper()
        storageCooldown = None
        

        # get storageCooldown value from lua file
        with open(monsterLoc) as file:
            copying = False
            braces = 0
            for line in file:
                if 'storageCooldown' in line:
                    storageCooldown = line.split('=')[1].strip()
                    break

        bosstiary = 'monster.bosstiary = {\n'
        bosstiary += '\tbossRaceId = ' + str(bossid) + ',\n'
        bosstiary += '\trarity = ' + rarity + ',\n'
        if storageCooldown:
            bosstiary += '\tstorageCooldown = ' + storageCooldown + ',\n'
        bosstiary += '}\n'

else:
    ### RACEID
    raceid = ''
    if ('race_id' in data):
        raceid = 'monster.raceId = ' + str(data['race_id']) + '\n'


    ### BESTIARY
    beastiary = ''
    if ('bestiarylevel' in data):
        beastiaryLevel = data['bestiarylevel']
        toKill = 0
        firstUnlock = 0
        secondUnlock = 0
        charmPoints = 0
        stars = 0
        occurrence = data['occurrence']
        occurrenceLevel = 0
        location = data.setdefault('location', '')
        location = re.sub(r'[^A-Za-z0-9 ,.-]+', '', location)

        if (beastiaryLevel != 'Very Rare'):
            if (beastiaryLevel == 'Harmless'):
                toKill = 25
                firstUnlock = 5
                secondUnlock = 10
                charmPoints = 1
                stars = 0
            elif (beastiaryLevel == 'Trivial'):
                toKill = 250
                firstUnlock = 10
                secondUnlock = 100
                charmPoints = 5
                stars = 1
            elif (beastiaryLevel == 'Easy'):
                toKill = 500
                firstUnlock = 25
                secondUnlock = 250
                charmPoints = 15
                stars = 2
            elif (beastiaryLevel == 'Medium'):
                toKill = 1000
                firstUnlock = 50
                secondUnlock = 500
                charmPoints = 25
                stars = 3
            elif (beastiaryLevel == 'Hard'):
                toKill = 2500
                firstUnlock = 100
                secondUnlock = 1000
                charmPoints = 50
                stars = 4
            elif (beastiaryLevel == 'Challenging'):
                toKill = 5000
                firstUnlock = 200
                secondUnlock = 2000
                charmPoints = 100
                stars = 5
        else:
            toKill = 5
            firstUnlock = 2
            secondUnlock = 5
            if (beastiaryLevel == 'Harmless'):
                charmPoints = 5
                stars = 0
            elif (beastiaryLevel == 'Trivial'):
                charmPoints = 10
                stars = 1
            elif (beastiaryLevel == 'Easy'):
                charmPoints = 30
                stars = 2
            elif (beastiaryLevel == 'Medium'):
                charmPoints = 50
                stars = 3
            elif (beastiaryLevel == 'Hard'):
                charmPoints = 100
                stars = 4
            elif (beastiaryLevel == 'Challenging'):
                charmPoints = 200
                stars = 5

        if (occurrence == 'Common'):
            occurrenceLevel = 0
        elif (occurrence == 'Uncommon'):
            occurrenceLevel = 1
        elif (occurrence == 'Rare'):
            occurrenceLevel = 2
        elif (occurrence == 'Very Rare'):
            occurrenceLevel = 3


        bRace = ''
        with open(monsterLoc) as file:
            for line in file:
                if (line.rstrip().startswith("\trace = ")):
                    bRace = line.rstrip()

        beastiary = 'monster.Bestiary = {\n'
        beastiary += '\tclass = "' + str(data['bestiaryclass']) + '",\n'
        beastiary += bRace + '\n'
        beastiary += '\ttoKill = ' + str(toKill) + ',\n'
        beastiary += '\tFirstUnlock = ' + str(firstUnlock) + ',\n'
        beastiary += '\tSecondUnlock = ' + str(secondUnlock) + ',\n'
        beastiary += '\tCharmsPoints = ' + str(charmPoints) + ',\n'
        beastiary += '\tStars = ' + str(stars) + ',\n'
        beastiary += '\tOccurrence = ' + str(occurrenceLevel) + ',\n'
        beastiary += '\tLocations = "' + location + '"\n'
        beastiary += '}\n'


### HEALTH
if ('hp' in data):
    health = 'monster.health = ' + str(data['hp']) + '\n'
else: 
    with open(monsterLoc) as file:
        for line in file:
            if (line.rstrip().startswith("monster.health = ")):
                health = line.rstrip() + '\n'


### MAX HEALTH
if 'hp' in data:
    maxHealth = 'monster.maxHealth = ' + str(data['hp']) + '\n'
else:
    with open(monsterLoc) as file:
        for line in file:
            if (line.rstrip().startswith("monster.maxHealth = ")):
                maxHealth = line.rstrip() + '\n'


### RACE
mRace = ''
with open(monsterLoc) as file:
    for line in file:
        if (line.rstrip().startswith("monster.race = ")):
            mRace = line.rstrip()

race = mRace + '\n'


### CORPSE
mCorpse = ''
with open(monsterLoc) as file:
    for line in file:
        if (line.rstrip().startswith("monster.corpse = ")):
            mCorpse = line.rstrip()

corpse = mCorpse + '\n'


### SPEED
if ('speed' in data):
    speed = 'monster.speed = ' + str(data['speed']) + '\n'
else:
    with open(monsterLoc) as file:
        for line in file:
            if (line.rstrip().startswith("monster.speed = ")):
                speed = line.rstrip() + '\n'


### MANA COST
if (data['summon'].isnumeric()):
    manaCost = 'monster.manaCost = ' + str(data['summon']) + '\n'
elif (data['convince'].isnumeric()):
    manaCost = 'monster.manaCost = ' + str(data['convince']) + '\n'
else:
    manaCost = 'monster.manaCost = 0\n'


### FACTION
faction = ''
with open(monsterLoc) as file:
    for line in file:
        if (line.rstrip().startswith("monster.faction = ")):
            faction = line.rstrip() + '\n'


### ENEMY FACTIONS
enemyFactions = ''
with open(monsterLoc) as file:
    for line in file:
        if (line.rstrip().startswith("monster.enemyFactions = ")):
            enemyFactions = line.rstrip() + '\n'


### CHANGE TARGET
changeTarget = ''

with open(monsterLoc) as file:
    copying = False
    braces = 0
    for line in file:
        lineStr = line.rstrip()
        if (copying):
            braces += lineStr.count('{')
            braces -= lineStr.count('}')
            if (braces < 1):
                copying = False
                break
            changeTarget += lineStr + '\n'
        if (lineStr.startswith("monster.changeTarget = ")):
            braces += 1
            copying = True
            changeTarget += lineStr + '\n'

changeTarget += '}\n'


### STRATEGIES
strategies = ''

with open(monsterLoc) as file:
    copying = False
    braces = 0
    for line in file:
        lineStr = line.rstrip()
        if (copying):
            braces += lineStr.count('{')
            braces -= lineStr.count('}')
            if (braces < 1):
                copying = False
                break
            strategies += lineStr + '\n'
        if (lineStr.startswith("monster.strategiesTarget = ")):
            braces += 1
            copying = True
            strategies += lineStr + '\n'

strategies += '}\n'

### FLAGS still need to parse json values for these
summonable = 'false'
convince = 'false'
pushable = 'false'
isBoss = 'false'
illusionable = 'false'
pushObjects = 'true'
if 'hp' in data:
    runsAt = data['hp']
else:
    with open(monsterLoc) as file:
        for line in file:
            if (line.rstrip().startswith("\trunHealth = ")):
                runsAt = line.rstrip()
            

summonable = 'true' if data.setdefault('summon', '0').isnumeric() else 'false'
convince = 'true' if data.setdefault('convince', '0').isnumeric() else 'false'
pushable = 'true' if data.setdefault('pushable', 'no').lower() == 'yes' else 'false'
isBoss = 'true' if data.setdefault('isboss', 'no').lower() == 'yes' else 'false'
illusionable = 'true' if data.setdefault('illusionable', 'no').lower() == 'yes' else 'false'
pushObjects = 'false' if data.setdefault('pushobjects', 'yes').lower() == 'no' else 'true'

canWalkOnEnergy = 'true'
canWalkOnFire = 'true'
canWalkOnPoison = 'true'
if ('walksthrough' in data):
    walkData = data['walksthrough'].lower()
    if "?" not in walkData:
        if("fire" not in walkData):
            canWalkOnFire = 'false'
        if("poison" not in walkData):
            canWalkOnPoison = 'false'
        if('energy' not in walkData):
            canWalkOnEnergy = 'false'

if ('walksaround' in data):
    walkData = data['walksaround'].lower()
    if("fire" in walkData):
        canWalkOnFire = 'false'
    if("poison" in walkData):
        canWalkOnPoison = 'false'
    if('energy' in walkData):
        canWalkOnEnergy = 'false'


attackable = ''
hostile = ''
canPushCreatures = ''
staticAttackChance = ''
targetDistance = ''
healthHidden = ''
isBlockable = ''
runHealth = ''
pet = ''

#get from lua file
    #attackable
    #hostile
    #canPushCreatures
    #staticAttackChance
    #targetDistance
    #healthHidden
    #isBlockable
    #runHealth
    #pet

with open(monsterLoc) as file:
    for line in file:
        lineStr = line.rstrip()
        if (lineStr.startswith("\tattackable = ")):
            attackable = lineStr
        if (lineStr.startswith("\thostile = ")):
            hostile = lineStr
        if (lineStr.startswith("\tcanPushCreatures = ")):
            canPushCreatures = lineStr
        if (lineStr.startswith("\tstaticAttackChance = ")):
            staticAttackChance = lineStr
        if (lineStr.startswith("\ttargetDistance = ")):
            targetDistance = lineStr
        if (lineStr.startswith("\thealthHidden = ")):
            healthHidden = lineStr
        if (lineStr.startswith("\tisBlockable = ")):
            isBlockable = lineStr
        if (lineStr.startswith("\trunHealth = ")):
            runHealth = lineStr
        if (lineStr.startswith("\tpet = ")):
            pet = lineStr


flags = 'monster.flags = {\n'
flags += '\tsummonable = ' + summonable + ',\n'
flags += attackable + '\n'
flags += hostile + '\n'
flags += '\tconvinceable = ' + convince + ',\n'
flags += '\tpushable = ' + pushable + ',\n'
flags += '\trewardBoss = ' + isBoss + ',\n'
flags += '\tillusionable = ' + illusionable + ',\n'
flags += '\tcanPushItems = ' + pushObjects + ',\n'
flags += canPushCreatures + '\n'
flags += staticAttackChance + '\n'
flags += targetDistance + '\n'
flags += runHealth + '\n'
flags += healthHidden + '\n'
flags += isBlockable + '\n'
flags += '\tcanWalkOnEnergy = ' + canWalkOnEnergy + ',\n'
flags += '\tcanWalkOnFire = ' + canWalkOnFire + ',\n'
flags += '\tcanWalkOnPoison = ' + canWalkOnPoison + ',\n'
if (pet != ''):
    flags += pet + '\n'
flags += '}\n'


### LIGHT currently using 'lightcolor' and 'lightradius' for color and level. this may be incorrect.
lightLevel = 0
lightColor = 0
if not data.get('lightradius') is None:
    lightLevel = data['lightradius']

if not data.get('lightcolor') is None:
    lightColor = data['lightcolor']

light = 'monster.light = {\n'
light += '\tlevel = ' + str(lightLevel) + ',\n'
light += '\tcolor = ' + str(lightColor) + ',\n'
light += '}\n'


### SUMMONS
summons = ''
with open(monsterLoc) as file:
    braces = 0
    copying = False
    for line in file:
        lineStr = line.rstrip()
        if (copying):
            braces += lineStr.count('{')
            braces -= lineStr.count('}')
            summons += lineStr + '\n'
            if (braces < 1):
                copying = False
                break
        if (lineStr.startswith("monster.summon = ")):
            braces += 1
            copying = True
            summons += lineStr + '\n'


### VOICES
voiceLines = data.setdefault('sounds', [])
voices = 'monster.voices = {\n'
voices += '\tinterval = 5000,\n'
voices += '\tchance = 10,\n'

for line in voiceLines:
    if (line == ''):
        break
    if (line.isupper()):
        yell = 'true'
    else:
        yell = 'false'
            
    voices += '\t{text = "' + line + '", yell = ' + yell + '},\n'

voices += '}\n'

### LOOT maybe populate loot with item from json
loot = ''
with open(monsterLoc) as file:
    copying = False
    braces = 0
    for line in file:
        lineStr = line.rstrip()
        if (copying):
            braces += lineStr.count('{')
            braces -= lineStr.count('}')
            if (braces < 1):
                copying = False
                break
            loot += lineStr + '\n'
        if (lineStr.startswith("monster.loot = ")):
            braces += 1
            copying = True
            loot += lineStr + '\n'

loot += '}\n'

### ATTACKS  add abilities from json as comments to make visual check easier
attacks = ''
if ('abilities' in data):
    parsedAbilityList = abilities_as_lua(format_abilities(str(data['abilities'])))
    parsedAbilityList += '\n'
    with open(monsterLoc) as file:
        copying = False
        braces = 0
        for line in file:
            lineStr = line.rstrip()
            if (copying):
                braces += lineStr.count('{')
                braces -= lineStr.count('}')
                if (braces < 1):
                    copying = False
                    attacks += lineStr + '\n'
                    break
                else: 
                    attacks += lineStr + '\n'
            if (lineStr.startswith("monster.attacks = ")):
                copying = True
                braces += 1
                attacks += lineStr + '\n'


### DEFENSES
defenses = ''
with open(monsterLoc) as file:
    copying = False
    braces = 0
    for line in file:
        lineStr = line.rstrip()
        if (copying):
            braces += lineStr.count('{')
            braces -= lineStr.count('}')
            if (braces < 1):
                copying = False
                break
            if (lineStr.startswith('\tmitigation =')):
                pass
            elif (lineStr.startswith('\tdefense =')):
                defenses += lineStr + '\n'
            elif (lineStr.startswith('\tarmor')):
                if (data.setdefault('armor', '0').isnumeric()):
                    defenses += '\tarmor = ' + str(data['armor']) + ',\n'
                else:
                    with open(monsterLoc) as file:
                        for line in file:
                            lineStr = line.rstrip()
                            if (lineStr.startswith('\tarmor =')):
                                defenses += lineStr + '\n'
                if ('mitigation' in data):
                    defenses += '\tmitigation = ' + str(data['mitigation']) + ',\n'
                else:
                    defenses += '--\tmitigation = ???,\n'
            else:
                defenses += lineStr + '\n'
        if (lineStr.startswith("monster.defenses = ")):
            braces += 1
            copying = True
            defenses = lineStr + '\n'

defenses += '}\n'

### REFLECTS
reflects = ''

with open(monsterLoc) as file:
    copying = False
    braces = 0
    for line in file:
        lineStr = line.rstrip()
        if (copying):
            braces += lineStr.count('{')
            braces -= lineStr.count('}')
            if (braces < 1):
                copying = False
                break
            reflects += lineStr + '\n'
        if (lineStr.startswith("monster.reflects = ")):
            braces += 1
            copying = True
            reflects += lineStr + '\n'

if (len(reflects) > 0):
    reflects += '}\n\n'


### RESISTANCES
physicalResistance = data["physicalDmgMod"]
energyResistance = data["energyDmgMod"]
earthResistance = data["earthDmgMod"]
fireResistance = data["fireDmgMod"]
lifeDrainResistance = data.setdefault("hpDrainDmgMod", "0")
drownDmgResistance = data["drownDmgMod"]
iceResistance = data["iceDmgMod"]
holyResistance = data["holyDmgMod"]
deathResistance = data["deathDmgMod"]

physicalResistance = re.sub('[^0-9]', '', physicalResistance)
energyResistance = re.sub('[^0-9]', '', energyResistance)
earthResistance = re.sub('[^0-9]', '', earthResistance)
fireResistance = re.sub('[^0-9]', '', fireResistance)
lifeDrainResistance = re.sub('[^0-9]', '', lifeDrainResistance)
drownDmgResistance = re.sub('[^0-9]', '', drownDmgResistance)
iceResistance = re.sub('[^0-9]', '', iceResistance)
holyResistance = re.sub('[^0-9]', '', holyResistance)
deathResistance = re.sub('[^0-9]', '', deathResistance)

physicalResistance = 100 - int(physicalResistance)
energyResistance = 100 - int(energyResistance)
earthResistance = 100 - int(earthResistance)
fireResistance = 100 - int(fireResistance)
lifeDrainResistance = 100 - int(lifeDrainResistance)
drownDmgResistance = 100 - int(drownDmgResistance)
iceResistance = 100 - int(iceResistance)
holyResistance = 100 - int(holyResistance)
deathResistance = 100 - int(deathResistance)

resistances = 'monster.elements = {\n'
resistances += '\t{type = COMBAT_PHYSICALDAMAGE, percent = ' + str(physicalResistance) + '},\n'
resistances += '\t{type = COMBAT_ENERGYDAMAGE, percent = '+ str(energyResistance) + '},\n'
resistances += '\t{type = COMBAT_EARTHDAMAGE, percent = '+ str(earthResistance) + '},\n'
resistances += '\t{type = COMBAT_FIREDAMAGE, percent = '+ str(fireResistance) + '},\n'
resistances += '\t{type = COMBAT_LIFEDRAIN, percent = '+ str(lifeDrainResistance) + '},\n'
resistances += '\t{type = COMBAT_MANADRAIN, percent = 0},\n'
resistances += '\t{type = COMBAT_DROWNDAMAGE, percent = ' + str(drownDmgResistance) + '},\n'
resistances += '\t{type = COMBAT_ICEDAMAGE, percent = ' + str(iceResistance) + '},\n'
resistances += '\t{type = COMBAT_HOLYDAMAGE, percent = ' + str(holyResistance) + '},\n'
resistances += '\t{type = COMBAT_DEATHDAMAGE, percent = ' + str(deathResistance) + '},\n'
resistances += '}\n'


### IMMUNITIES
paralyzeImmunity = 'false' if data.setdefault('paraimmune', 'yes').lower() == 'no' else 'true'
invisibleImmunity = 'false' if data.setdefault('senseinvis', 'yes').lower() == 'no' else 'true'

outfitImmunity = ''
bleed = ''
with open(monsterLoc) as file:
    for line in file:
        lineStr = line.rstrip()
        if (lineStr.startswith("\t{type = \"outfit\",")):
            outfitImmunity = lineStr + '\n'
        if (lineStr.startswith("\t{type = \"bleed\",")):
            bleed = lineStr + '\n'

immunities = 'monster.immunities = {\n'
immunities += '\t{type = "paralyze", condition = ' + paralyzeImmunity + '},\n'
immunities += outfitImmunity
immunities += '\t{type = "invisible", condition = ' + invisibleImmunity + '},\n'
immunities += bleed
immunities += '}\n'

### CALLBACKS

callbacks = ''

# copy callbacks from original file
with open(monsterLoc) as file:
    copying = False
    for line in file:
        lineStr = line.rstrip()
        if copying:
            if lineStr.startswith("mType:register"):
                copying = False
                break
            callbacks += lineStr + '\n'
        elif (lineStr.startswith("mType.on")):
            braces += 1
            copying = True
            callbacks += lineStr + '\n'

### REGISTER
register = 'mType:register(monster)\n'


result = variables + "\n" + description + experience + outfit + "\n" + bosstiary + raceid + beastiary + "\n" + health + maxHealth + race + corpse + speed + manaCost + "\n" + faction + enemyFactions + "\n" + changeTarget + "\n" + strategies + "\n" + flags + "\n" + light + "\n" + summons + "\n" + voices + "\n" + loot + "\n" + parsedAbilityList +attacks + "\n" + defenses + "\n" + reflects + resistances + "\n" + immunities + "\n" + callbacks + "\n" + register

f = open(str(monsterLoc), 'w')
f.write(remove_consecutive_linebreaks(result))
f.close()
