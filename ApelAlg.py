from pymei import *
from fractions import *

# Functions about preceeding and suceeding elements
def get_peer_index(target_element):
    peers = target_element.getPeers()
    i = 0
    for element in peers:
        if element == target_element:
            index = i
            break
        i += 1
    return [index, peers]

def get_next_element(target_element):
    [index, peers] = get_peer_index(target_element)
    try:
        next_element = peers[index + 1]
    except:
        next_element = None
    return next_element

def get_preceding_element(target_element):
    [index, peers] = get_peer_index(target_element)
    try:
        preceding_element = peers[index - 1]
    except:
        preceding_element = None
    return preceding_element

# Functions related to dots
def followed_by_dot(target_element):
    next_element = get_next_element(target_element)
    if next_element is not None and next_element.name == 'dot':
        return True
    else:
        return False

def find_first_dotted_note(sequence_of_notes):
    """Return the index of the first dotted note in a sequence of notes"""
    note_counter = -1
    first_dotted_note_index = -1
    for noterest in sequence_of_notes:
        note_counter += 1
        if noterest is not None and followed_by_dot(noterest):
            first_dotted_note_index = note_counter
            break
    return first_dotted_note_index

# Functions related to the counting of minims in a sequence of notes
def counting_minims_in_an_undotted_sequence(sequence_of_notes, note_durs, undotted_note_gain):
    minim_counter = 0
    for note in sequence_of_notes:
        dur = note.getAttribute('dur').value
        try:
            index = note_durs.index(dur)
        except:
            print("MISTAKE\nNote/Rest element not considered: " + str(note) + ", with a duration @dur = " + dur)
        gain = undotted_note_gain[index]
        if note.hasAttribute('num') and note.hasAttribute('numbase'):
            ratio = Fraction(int(note.getAttribute('numbase').value), int(note.getAttribute('num').value))
            gain *= ratio
        else:
            pass
        minim_counter += gain
    return minim_counter

def counting_minims(sequence_of_notes, note_durs, undotted_note_gain, dotted_note_gain):
    minim_counter = 0
    for note in sequence_of_notes:
        dur = note.getAttribute('dur').value
        try:
            index = note_durs.index(dur)
        except:
            print("MISTAKE\nNote/Rest element not considered: " + str(note) + ", with a duration @dur = " + dur)
        # Defining the gain in case of dotted or undotted notes:
        if followed_by_dot(note):
            gain = dotted_note_gain[index]
            # This dot could be either of perfection or of augmentation. 
            # In the case of a dot of perfection there is no need to do anything, as the note value is kept perfect.
            # In the case of a dot of augmentation, the note value should be changed from imperfect to perfect.
            if (index == 1 and prolatio == 2) or (index == 2 and tempus == 2) or (index > 1):
            ## NOTE TO SELF: ##
            #### Right now index == 1, is the index of prolatio. ####
            #### If later I put prolatio in a higher index like n, ####
            #### the information in this if should change accordingly. ####
                # Case: Dot of Augmentation
                # Encode the augmentation dot
                dot_element = get_next_element(note)
                dot_element.addAttribute('form', 'aug')
                # Perform the augmentation, multiply the note value by 1.5
                note.addAttribute('num', '2')
                note.addAttribute('numbase', '3')
                # Thus the default "imperfect" note, becomes a perfect note
                note.addAttribute('quality', 'p')
            else:
                pass
        else:
            gain = undotted_note_gain[index]
            if note.hasAttribute('num') and note.hasAttribute('numbase'):
                ratio = Fraction(int(note.getAttribute('numbase').value), int(note.getAttribute('num').value))
                gain *= ratio
            else:
                pass
        minim_counter += gain
    return minim_counter

# Given the total amount of "breves" in-between the "longs", see if they can be arranged in groups of 3
# According to how many breves remain ungrouped (1, 2 or 0), modifiy the duration of the appropriate note of the sequence ('imperfection', 'alteration', no-modification)
def modification(counter, start_note, middle_notes, end_note, following_note, short_note, long_note):
    # 1 breve left out:
    if counter % 3 == 1:
        # Default Case
        if start_note is not None and start_note.name == 'note' and start_note.getAttribute('dur').value == long_note and not start_note.hasAttribute('quality') and not followed_by_dot(start_note):
            # Imperfection a.p.p.
            start_note.addAttribute('quality', 'i')
            start_note.addAttribute('num', '3')
            start_note.addAttribute('numbase', '2')
        # Exception Case
        elif end_note is not None and end_note.name == 'note' and end_note.getAttribute('dur').value == long_note and not end_note.hasAttribute('quality') and not followed_by_dot(end_note):
            # Imperfection a.p.a.
            end_note.addAttribute('quality', 'i')
            end_note.addAttribute('num', '3')
            end_note.addAttribute('numbase', '2')
            # Raise a warning when this imperfect note is followed by a perfect note (contradiction with the first rule)
            if following_note is not None and following_note.getAttribute('dur').value == long_note:
                print("WARNING! An imperfection a.p.a. is required, but this imperfect note is followed by a perfect note, this contradicts the fundamental rule: 'A note is perfect before another one of the same kind'.")
                print("The imperfected note is " + str(end_note) + " and is followed by the perfect note " + str(following_note))
                print("")
        # Mistake Case
        else:
            print("MISTAKE 1 - Impossible to do Imperfection a.p.p. and also Imperfection a.p.a.")
            print(start_note)
            print(end_note)
            print("")

    # 2 breves left out:
    elif counter % 3 == 2:
        before_last = middle_notes[-1]
        # 2 exact breves between the longs
        if counter == 2:
            # Default case
            if before_last.name == 'note' and before_last.getAttribute('dur').value == short_note and not before_last.hasAttribute('quality'):
                # Alteration
                before_last.addAttribute('quality', 'a')
                before_last.addAttribute('num', '1')
                before_last.addAttribute('numbase', '2')
            # Exception Case
            elif (start_note is not None and start_note.name == 'note' and start_note.getAttribute('dur').value == long_note and not start_note.hasAttribute('quality') and not followed_by_dot(start_note)) and (end_note is not None and end_note.name == 'note' and end_note.getAttribute('dur').value == long_note and not end_note.hasAttribute('quality') and not followed_by_dot(end_note)):
                # Imperfection a.p.p. 
                start_note.addAttribute('quality', 'i')
                start_note.addAttribute('num', '3')
                start_note.addAttribute('numbase', '2')
                # Imperfection a.p.a.
                end_note.addAttribute('quality', 'i')
                end_note.addAttribute('num', '3')
                end_note.addAttribute('numbase', '2')
                # Raise a warning when this imperfect note is followed by a perfect note (contradiction with the first rule)
                if following_note is not None and following_note.getAttribute('dur').value == long_note:
                    print("WARNING! An imperfection a.p.a. is required, but this imperfect note is followed by a perfect note, this contradicts the fundamental rule: 'A note is perfect before another one of the same kind'.")
                    print("The imperfected note is " + str(end_note) + " and is followed by the perfect note " + str(following_note))
                    print("")
            # Mistake Case
            else:
                print("MISTAKE 2 - Alteration is impossible - Imperfections a.p.p. and a.p.a. are also impossible")
                print(start_note)
                print(end_note)
                print("")
        # 5, 8, 11, 14, 17, 20, ... breves between the longs
        else:
            # Default case
            if (start_note is not None and start_note.name == 'note' and start_note.getAttribute('dur').value == long_note and not start_note.hasAttribute('quality') and not followed_by_dot(start_note)) and (end_note is not None and end_note.name == 'note' and end_note.getAttribute('dur').value == long_note and not end_note.hasAttribute('quality') and not followed_by_dot(end_note)):
                # Imperfection a.p.p. 
                start_note.addAttribute('quality', 'i')
                start_note.addAttribute('num', '3')
                start_note.addAttribute('numbase', '2')
                # Imperfection a.p.a.
                end_note.addAttribute('quality', 'i')
                end_note.addAttribute('num', '3')
                end_note.addAttribute('numbase', '2')
                # Raise a warning when this imperfect note is followed by a perfect note (contradiction with the first rule)
                if following_note is not None and following_note.getAttribute('dur').value == long_note:
                    print("WARNING! An imperfection a.p.a. is required, but this imperfect note is followed by a perfect note, this contradicts the fundamental rule: 'A note is perfect before another one of the same kind'.")
                    print("The imperfected note is " + str(end_note) + " and is followed by the perfect note " + str(following_note))
                    print("")
            # Exception Case
            elif before_last.name == 'note' and before_last.getAttribute('dur').value == short_note and not before_last.hasAttribute('quality'):
                # Alteration
                before_last.addAttribute('quality', 'a')
                before_last.addAttribute('num', '1')
                before_last.addAttribute('numbase', '2')
            # Mistake Case
            else:
                print("MISTAKE 2 - Imperfections a.p.p. and a.p.a. are impossible - Alteration is also impossible")
                print(start_note)
                print(end_note)
                print("")
    
    # 0 breves left out:
    else:
        pass

def minims_between_semibreves(start_note, middle_notes, end_note, following_note):
    # Counting notes in between the extremes
    note_durs = ['minima']
    undotted_note_gain = [1]
    dotted_note_gain = [1.5]

    minim_counter = counting_minims(middle_notes, note_durs, undotted_note_gain, dotted_note_gain)

    # Given the total amount of minims in-between the "semibreves", see if they can be arranged in groups of 3
    # According to how many minims remain ungrouped (1, 2 or 0), modifiy the duration of the appropriate note of the sequence ('imperfection', 'alteration', no-modification)
    modification(minim_counter, start_note, middle_notes, end_note, following_note, 'minima', 'semibrevis')

def sb_between_breves(start_note, middle_notes, end_note, following_note):
    no_division_dot_flag = True    # Default value
    sequence = [start_note] + middle_notes
    first_dotted_note_index = find_first_dotted_note(sequence)

    note_durs = ['minima', 'semibrevis']
    undotted_note_gain = [1, prolatio]
    dotted_note_gain = [1.5, 3]

    # If first_dotted_note_index == -1, then there is no dot in the sequence at all
    if first_dotted_note_index == -1:
        # Getting the total of semibreves in the middle_notes
        minim_counter = counting_minims_in_an_undotted_sequence(middle_notes, note_durs, undotted_note_gain)
        count_Sb = minim_counter / (prolatio)
        #print('No-dot\n')

    # If first_dotted_note_index == 0, we have a dot at the start_note, which will make this note 'perfect' --> DOT OF PERFECTION. The other dots must be of augmentation (or perfection dots).
    elif first_dotted_note_index == 0:
        # DOT OF PERFECTION
        dot_element = get_next_element(start_note)
        dot_element.addAttribute('form', 'perf')
        #print('Perfection\n')
        # Getting the total of semibreves in the middle_notes
        minim_counter = counting_minims(middle_notes, note_durs, undotted_note_gain, dotted_note_gain)
        count_Sb = minim_counter / (prolatio)

    # Otherwise, if the dot is in any middle note:
    else:
        # We have to divide the sequence of middle_notes in 2 parts: before the dot, and after the dot.
        # Then count the number of semibreves in each of the two parts to discover if this 'dot' is a 
        # 'dot of division' or a 'dot of addition'
        part1_middle_notes = sequence[1 : first_dotted_note_index + 1]
        part2_middle_notes = sequence[first_dotted_note_index + 1 : len(sequence)]

        # Semibreves BEFORE the first dot
        minim_counter1 = counting_minims_in_an_undotted_sequence(part1_middle_notes, note_durs, undotted_note_gain)
        part1_count_Sb = minim_counter1 / float(prolatio)

        # The individual value of the first dotted note (the last note in the sequence preceding the dot)
        first_dotted_note = part1_middle_notes[-1]
        dur = first_dotted_note.getAttribute('dur').value
        first_dotted_note_default_gain = undotted_note_gain[note_durs.index(dur)]
        #print("Notes in the Sequence preceeding this dot " + str(part1_middle_notes))
        #print("FIRST DOTTED NOTE: " + str(first_dotted_note) + ", with duration of: " + dur + ", which gain is: " + str(first_dotted_note_default_gain))

        # Taking the second part of the sequence of the middle notes (part2_middle_notes) into account
        # Count the number of semibreves in the second part of the sequence of middle_notes
        minim_counter2 = counting_minims(part2_middle_notes, note_durs, undotted_note_gain, dotted_note_gain)
        part2_count_Sb = minim_counter2 / float(prolatio)


        # If there is just one semibreve before the first dot
        if part1_count_Sb == 1:
            # Two possibilities: dot of division / dot of augmentation
            # We have to use the results of the second part of the middle notes (part2_middle_notes) to figure this out

            # If the number of semibreves after the dot is an integer number
            if part2_count_Sb == int(part2_count_Sb):
                # DOT OF DIVISION
                no_division_dot_flag = False
                #print('Imperfection app\n')
                dot_element = get_next_element(first_dotted_note)
                dot_element.addAttribute('form', 'div')
                minim_counter = minim_counter1 + minim_counter2
                # Total of semibreves in the middle_notes
                modification(part1_count_Sb, start_note, part1_middle_notes, None, None, 'semibrevis', 'brevis')
                modification(part2_count_Sb, None, part2_middle_notes, end_note, following_note, 'semibrevis', 'brevis')
            else:
                # DOT OF AUGMENTATION
                #print('Augmentation_typeI\n')
                dot_element = get_next_element(first_dotted_note)
                dot_element.addAttribute('form', 'aug')
                first_dotted_note.addAttribute('quality', 'p')
                first_dotted_note.addAttribute('num', '2')
                first_dotted_note.addAttribute('numbase', '3')
                minim_counter = minim_counter1 + (0.5 * first_dotted_note_default_gain) + minim_counter2
                pass

        # If there is more than one semibreve before the first dot, it is impossible for that dot to be a 'dot of division'
        else:
            # DOT OF AUGMENTATION
            #print('Augmentation_def\n')
            dot_element = get_next_element(first_dotted_note)
            dot_element.addAttribute('form', 'aug')
            first_dotted_note.addAttribute('quality', 'p')
            first_dotted_note.addAttribute('num', '2')
            first_dotted_note.addAttribute('numbase', '3')
            minim_counter = minim_counter1 + (0.5 * first_dotted_note_default_gain) + minim_counter2
            pass

        # Total of semibreves in the middle_notes
        count_Sb = minim_counter / prolatio

    if no_division_dot_flag:
        # Checking that the sequence of notes is fine, and then calling the modification function
        if(minim_counter % prolatio == 0):
            #print("GOOD")
            pass
        else:
            print("BAD! THE DIVISION IS NOT AN INTEGER NUMBER - not an integer number of Semibreves!")
            print([start_note] + middle_notes + [end_note])
            print("Semibreves: " + str(minim_counter / float(prolatio)))
        # Given the total amount of semibreves in-between the "breves", see if they can be arranged in groups of 3
        # According to how many semibreves remain ungrouped (1, 2 or 0), modifiy the duration of the appropriate note of the sequence ('imperfection', 'alteration', no-modification)
        modification(count_Sb, start_note, middle_notes, end_note, following_note, 'semibrevis', 'brevis')

def breves_between_longas(start_note, middle_notes, end_note, following_note):
    no_division_dot_flag = True    # Default value
    sequence = [start_note] + middle_notes
    first_dotted_note_index = find_first_dotted_note(sequence)

    note_durs = ['minima', 'semibrevis', 'brevis']
    undotted_note_gain = [1, prolatio, tempus * prolatio]
    dotted_note_gain = [1.5, 3, 3 * prolatio]

    # If first_dotted_note_index == -1, then there is no dot in the sequence at all
    if first_dotted_note_index == -1:
        # Total of breves in the middle_notes
        minim_counter = counting_minims_in_an_undotted_sequence(middle_notes, note_durs, undotted_note_gain)
        count_B = minim_counter / (tempus * prolatio)
        #print('No-dot\n')

    # If first_dotted_note_index == 0, we have a dot at the start_note, which will make this note 'perfect' --> DOT OF PERFECTION. The other dots must be of augmentation (or perfection dots).
    elif first_dotted_note_index == 0:
        # DOT OF PERFECTION
        dot_element = get_next_element(start_note)
        dot_element.addAttribute('form', 'perf')
        #print('Perfection\n')
        # Total of breves in the middle_notes
        minim_counter = counting_minims(middle_notes, note_durs, undotted_note_gain, dotted_note_gain)
        count_B = minim_counter / (tempus * prolatio)

    # Otherwise, if the dot is in any middle note:
    else:
        # We have to divide the sequence of middle_notes in 2 parts: before the dot, and after the dot.
        # Then count the number of breves in each of the two parts to discover if this 'dot' is a 
        # 'dot of division' or a 'dot of addition'
        part1_middle_notes = sequence[1 : first_dotted_note_index + 1]
        part2_middle_notes = sequence[first_dotted_note_index + 1 : len(sequence)]

        # Breves BEFORE the first dot
        minim_counter1 = counting_minims_in_an_undotted_sequence(part1_middle_notes, note_durs, undotted_note_gain)
        part1_count_B = minim_counter1 / float(tempus*prolatio)
        
        # The individual value of the first dotted note (the last note in the sequence preceding the dot)
        first_dotted_note = part1_middle_notes[-1]
        dur = first_dotted_note.getAttribute('dur').value
        first_dotted_note_default_gain = undotted_note_gain[note_durs.index(dur)]

        # Taking the second part of the sequence of the middle notes (part2_middle_notes) into account
        # Count the number of breves in the second part of the sequence of middle_notes
        minim_counter2 = counting_minims(part2_middle_notes, note_durs, undotted_note_gain, dotted_note_gain)
        part2_count_B = minim_counter2 / float(tempus*prolatio)

        # If there is just one breve before the first dot
        if part1_count_B == 1:
            # Two possibilities: dot of division / dot of augmentation
            # We have to take a look at the second part of the middle notes (part2_middle_notes) to figure this out

            # If the number of breves after the dot is an integer number
            if part2_count_B == int(part2_count_B):
                # DOT OF DIVISION
                no_division_dot_flag = False
                #print('Imperfection app\n')
                dot_element = get_next_element(first_dotted_note)
                dot_element.addAttribute('form', 'div')
                minim_counter = minim_counter1 + minim_counter2
                # Total of breves in the middle_notes
                modification(part1_count_B, start_note, part1_middle_notes, None, None, 'brevis', 'longa')
                modification(part2_count_B, None, part2_middle_notes, end_note, following_note, 'brevis', 'longa')
            else:
                # DOT OF AUGMENTATION
                #print('Augmentation_typeI\n')
                dot_element = get_next_element(first_dotted_note)
                dot_element.addAttribute('form', 'aug')
                first_dotted_note.addAttribute('quality', 'p')
                first_dotted_note.addAttribute('num', '2')
                first_dotted_note.addAttribute('numbase', '3')
                minim_counter = minim_counter1 + (0.5 * first_dotted_note_default_gain) + minim_counter2

        # If there is more than one breve before the first dot, it is impossible for that dot to be a 'dot of division'
        else:
            # DOT OF AUGMENTATION
            #print('Augmentation_def\n')
            dot_element = get_next_element(first_dotted_note)
            dot_element.addAttribute('form', 'aug')
            first_dotted_note.addAttribute('quality', 'p')
            first_dotted_note.addAttribute('num', '2')
            first_dotted_note.addAttribute('numbase', '3')
            minim_counter = minim_counter1 + (0.5 * first_dotted_note_default_gain) + minim_counter2

        # Total of breves in the middle_notes
        count_B = minim_counter / (tempus * prolatio)
        
    if no_division_dot_flag:
        # Checking that the sequence of notes is fine, and then calling the modification function
        if(minim_counter % (tempus * prolatio) == 0):
            #print("GOOD")
            pass
        else:
            print("BAD! THE DIVISION IS NOT AN INTEGER NUMBER - not an integer number of Breves!")
            print([start_note] + middle_notes + [end_note])
            print("Breves: " + str(minim_counter / float(tempus * prolatio)))
        # Given the total amount of breves in-between the "longas", see if they can be arranged in groups of 3
        # According to how many breves remain ungrouped (1, 2 or 0), modifiy the duration of the appropriate note of the sequence ('imperfection', 'alteration', no-modification)
        modification(count_B, start_note, middle_notes, end_note, following_note, 'brevis', 'longa')


# Remove the @quality, @num and @numbase attributes
file = raw_input("Piece: ")
doc = documentFromFile(file).getMeiDocument()
listNotesRests = doc.getElementsByName('note')
listNotesRests.extend(doc.getElementsByName('rest'))
for note_or_rest in listNotesRests:
    note_or_rest.removeAttribute('num')
    note_or_rest.removeAttribute('numbase')
    note_or_rest.removeAttribute('quality')
documentToFile(doc, file[:-4] + "_stg0.mei")

# For each voice (staff element) in the "score"
staves = doc.getElementsByName('staff')
stavesDef = doc.getElementsByName('staffDef')
for i in range(0, len(stavesDef)):
    print("\n\nVOICE # " + str(i+1) + "\n")
    staffDef = stavesDef[i]
    staff = staves[i]

    # Getting the mensuration information of the voice
    prolatio = int(staffDef.getAttribute('prolatio').value)
    tempus = int(staffDef.getAttribute('tempus').value)
    modusminor = int(staffDef.getAttribute('modusminor').value)
    modusmaior = int(staffDef.getAttribute('modusmaior').value)

    # Getting all the notes and rests of one voice into a python list, in order.
    # This allows to retrieve the index, which is not possible with MEI lists.
    voice_content = staff.getChildrenByName('layer')[0].getChildren()
    voice_noterest_content = []
    for element in voice_content:
        name = element.name
        if name == 'note' or name == 'rest':
            voice_noterest_content.append(element)
        else:
            #print(name)
            #print(element)
            #print ""
            pass
    #print(voice_noterest_content)

    # Find indices for starting and ending points of each sequence of notes to be analyzed.
    # Each of the following is a list of indices of notes greater or equal than: a Semibreve, a Breve, a Long and a Maxima, respectively.
    list_of_indices_geq_Sb = []
    list_of_indices_geq_B = []
    list_of_indices_geq_L = []
    list_of_indices_geq_Max = []
    # Get the indices
    for noterest in voice_noterest_content:
        dur = noterest.getAttribute('dur').value
        if dur == 'semibrevis':
            list_of_indices_geq_Sb.append(voice_noterest_content.index(noterest))
        elif dur == 'brevis':
            list_of_indices_geq_Sb.append(voice_noterest_content.index(noterest))
            list_of_indices_geq_B.append(voice_noterest_content.index(noterest))
        elif dur == 'longa':
            list_of_indices_geq_Sb.append(voice_noterest_content.index(noterest))
            list_of_indices_geq_B.append(voice_noterest_content.index(noterest))
            list_of_indices_geq_L.append(voice_noterest_content.index(noterest))
        elif dur == 'maxima':
            list_of_indices_geq_Sb.append(voice_noterest_content.index(noterest))
            list_of_indices_geq_B.append(voice_noterest_content.index(noterest))
            list_of_indices_geq_L.append(voice_noterest_content.index(noterest))
            list_of_indices_geq_Max.append(voice_noterest_content.index(noterest))
        else:
            #print("SHOULD BE A MINIM, IS IT?  It is " + dur)
            #print(noterest)
            #print ""
            pass

    # Minims in between semibreves (or higher note values)
    if prolatio == 3:
        print("\nSEMIBREVE GEQ")
        #print(list_of_indices_geq_Sb)
        #print ""

        if 0 not in list_of_indices_geq_Sb and list_of_indices_geq_Sb != []:
            start_note = None
            f = list_of_indices_geq_Sb[0]
            end_note = voice_noterest_content[f]
            try:
                following_note = voice_noterest_content[f+1]
            except:
                following_note = None
            middle_notes = voice_noterest_content[0:f]
            #print(start_note)
            #print(middle_notes)
            #print(end_note)
            minims_between_semibreves(start_note, middle_notes, end_note, following_note)

        for i in range(0, len(list_of_indices_geq_Sb)-1):
            # Define the sequence of notes
            o = list_of_indices_geq_Sb[i]
            start_note = voice_noterest_content[o]
            f = list_of_indices_geq_Sb[i+1]
            end_note = voice_noterest_content[f]
            try:
                following_note = voice_noterest_content[f+1]
            except:
                following_note = None
            middle_notes = voice_noterest_content[o+1:f]
            #print(start_note)
            #print(middle_notes)
            #print(end_note)
            minims_between_semibreves(start_note, middle_notes, end_note, following_note)
    
    # prolatio = 2
    else:
        pass

    # Semibreves in between breves (or higher note values)
    if tempus == 3:
        print("\nBREVE GEQ")
        #print(list_of_indices_geq_B)
        #print ""

        if 0 not in list_of_indices_geq_B and list_of_indices_geq_B != []:
            start_note = None
            f = list_of_indices_geq_B[0]
            end_note = voice_noterest_content[f]
            try:
                following_note = voice_noterest_content[f+1]
            except:
                following_note = None
            middle_notes = voice_noterest_content[0:f]
            #print(start_note)
            #print(middle_notes)
            #print(end_note)
            sb_between_breves(start_note, middle_notes, end_note, following_note)

        for i in range(0, len(list_of_indices_geq_B)-1):
            # Define the sequence of notes
            o = list_of_indices_geq_B[i]
            start_note = voice_noterest_content[o]
            f = list_of_indices_geq_B[i+1]
            end_note = voice_noterest_content[f]
            try:
                following_note = voice_noterest_content[f+1]
            except:
                following_note = None
            middle_notes = voice_noterest_content[o+1:f]
            #print(start_note)
            #print(middle_notes)
            #print(end_note)
            sb_between_breves(start_note, middle_notes, end_note, following_note)

    # tempus = 2
    else:
        pass

    # Breves in between longas (or higher note values)
    if modusminor == 3:
        print("\nLONGA GEQ")
        #print(list_of_indices_geq_L)
        #print ""

        if 0 not in list_of_indices_geq_L and list_of_indices_geq_L != []:
            start_note = None
            f = list_of_indices_geq_L[0]
            end_note = voice_noterest_content[f]
            try:
                following_note = voice_noterest_content[f+1]
            except:
                following_note = None
            middle_notes = voice_noterest_content[0:f]
            #print(start_note)
            #print(middle_notes)
            #print(end_note)
            breves_between_longas(start_note, middle_notes, end_note, following_note)

        for i in range(0, len(list_of_indices_geq_L)-1):
            # Define the sequence of notes
            o = list_of_indices_geq_L[i]
            start_note = voice_noterest_content[o]
            f = list_of_indices_geq_L[i+1]
            end_note = voice_noterest_content[f]
            try:
                following_note = voice_noterest_content[f+1]
            except:
                following_note = None
            middle_notes = voice_noterest_content[o+1:f]
            #print(start_note)
            #print(middle_notes)
            #print(end_note)
            breves_between_longas(start_note, middle_notes, end_note, following_note)

    # modusminor = 2
    else:
        pass

    # There are notes that, when dotted, the dot used must be a dot of augmentation
    # Only imperfect notes can be augmented by a dot, but not all dots in them are augmentation dots
    # These imperfect notes can be followed by a division dot, as they can form a perfection with a larger note.
    # If a note is perfect, by the functions above all the dotted notes with smaller values are examined to determine if the dot is a 'division dot' or an 'augmentation dot'
    # But in case of larger values, this is not evaluated.
    # The following code performs that action. It goes from 'maxima' to 'semibrevis', until if finds a perfect mensuration. 
    # All the notes larger than that perfect note are considered to be augmented by any dot following them.

    note_level = ['maxima', 'longa', 'brevis', 'semibrevis']
    mensuration = [modusmaior, modusminor, tempus, prolatio]
    notes_NoDivisionDot_possibility = []
    i = 0
    acum_boolean =  mensuration[0]
    while (acum_boolean % 2 == 0):
        notes_NoDivisionDot_possibility.append(note_level[i])
        i += 1
        try:
            acum_boolean += mensuration[i]
        except:
            break
    print(acum_boolean)
    print(notes_NoDivisionDot_possibility)
    if len(notes_NoDivisionDot_possibility) != 0:
        dots = staff.getDescendantsByName('dot')
        for dot in dots:
            dotted_note = get_preceding_element(dot)
            # The preceding element of a dot should be either a <note> or a <rest>, so the following variable (dur_dotted_note) should be well defined
            dur_dotted_note = dotted_note.getAttribute('dur').value
            if dur_dotted_note in notes_NoDivisionDot_possibility:
                # Augmentation dot
                dot.addAttribute('form', 'aug')
                dotted_note.addAttribute('quality', 'p')
                dotted_note.addAttribute('num', '2')
                dotted_note.addAttribute('numbase', '3')




    documentToFile(doc, file[:-4] + "_STG3.mei")