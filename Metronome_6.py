from psychopy import visual, core, event, gui, prefs
import csv
import os
import numpy as np

prefs.hardware['audioLib'] = ['pygame']  # or ['sounddevice', 'pyo']
from psychopy import sound

# Try initializing sound
try:
    metronome = sound.Sound(value='A', secs=0.1)
except Exception as e:
    print(f"Error initializing metronome sound: {e}")

# Task and Frequency Selection Dialog
task_dialog = gui.Dlg(title="Task and Frequency Selection")
task_dialog.addField("Choose task type:", choices=["Visual Pulsation", "Metronome", "Both"])
task_dialog.addField("Choose frequency:", choices=["Fast", "Slow"])
task_dialog.show()

if task_dialog.OK:
    task_type = task_dialog.data[0]
    frequency_choice = task_dialog.data[1]
else:
    core.quit()  # Exit if dialog is canceled

# Set beat interval based on frequency choice
if frequency_choice == "Fast":
    beat_interval = 0.6  # 600ms for fast
else:
    beat_interval = 1.2  # 1200ms for slow

# Participant Info Dialog
participant_dialog = gui.Dlg(title="Participant Info")
participant_dialog.addField("Participant ID:")
participant_dialog.addField("Participant age:")
participant_dialog.addField("Do you regularly play an instrument or sing?", choices=["Yes", "No"])
participant_dialog.show()

if participant_dialog.OK:
    participant_id = participant_dialog.data[0]
    participant_age = participant_dialog.data[1]
    musical_experience = participant_dialog.data[2]
else:
    core.quit()  # Exit if dialog is canceled
    
# Define fullscreen window
win = visual.Window(color=[-1, -1, -1], units="pix", fullscr=True)

# Define text stimuli
instruction_text = visual.TextStim(win, text="Tap the spacebar to the beat you feel.\n\nPress 'space' to start.", 
                                   color="white", height=40, wrapWidth=800)
pause_text = visual.TextStim(win, text="Get ready!\n\nWatch the screen and follow the rhythm without tapping any key.\n\nFeel free to move though!",
                             color="white", height=40, wrapWidth=800)
pause2_text = visual.TextStim(win, text="Now verbally describe the picture shown.\n\n Take your time and, once done press the right arrow to progress to the next.",
                              color="white", height=40, wrapWidth=800)   
instruction2_text = visual.TextStim(win, text="Now, please try to replicate the rhythm you tapped earlier.\n\nPress 'space' to start.", 
                                   color="white", height=40, wrapWidth=800)                            

end_text = visual.TextStim(win, text="Thank you! The experiment is over.", color="white", height=30)

# Define the pulsating circle
circle = visual.Circle(win, radius=80, fillColor='white', lineColor='white')

# Define fixation cross
fixation = visual.TextStim(win, text="+", color="white", height=150)

# Set up timing parameters
duration = 20  # Duration of each phase in seconds
image_task_duration = 30  # Time allocated for the image task (in seconds)

# Load image file names
image_folder = "./"  # Images are in the same folder as the program
image_files = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]

# Initialize clock
clock = core.Clock()

# Function to record key presses (tapping) with fixation cross
def record_tapping(clock, duration, task_name):
    tapping_data = []
    end_time = clock.getTime() + duration

    while clock.getTime() < end_time:
        # Draw the fixation cross
        fixation.draw()
        win.flip()

        # Check for key presses
        keys = event.getKeys(timeStamped=clock)
        for key, timestamp in keys:
            if key == 'space':
                tapping_data.append({'event': f'{task_name}_keypress', 'timestamp': timestamp})
            elif key == 'escape':  # Exit on 'escape' key
                win.close()
                core.quit()
    return tapping_data

# Function for the stimuli
def pulsating_circle(clock, metronome, duration, include_metronome=False):
    pulsation_data = []  # Store timestamps of events
    end_time = clock.getTime() + duration
    next_pulsation_time = clock.getTime()
    next_metronome_time = clock.getTime()

    print("Starting pulsating circle with optional metronome...")
    while clock.getTime() < end_time:
        current_time = clock.getTime()

        # Control the circle pulsation
        if task_type in ["Visual Pulsation", "Both"] and current_time >= next_pulsation_time:
            circle.setOpacity(1.0)  # Circle visible
            pulsation_data.append({'event': 'pulsation', 'timestamp': current_time})
            next_pulsation_time += beat_interval  # Schedule next pulsation

        # Fade out the circle halfway through the interval
        if current_time >= next_pulsation_time - (beat_interval / 2):
            circle.setOpacity(0.0)  # Circle invisible

        circle.draw()

        # Control the metronome sound
        if include_metronome and task_type in ["Metronome", "Both"] and current_time >= next_metronome_time:
            metronome.play()  # Play the metronome sound
            core.wait(beat_interval - 0.1)  # Wait for the rest of the interval minus sound duration
            metronome.stop()  # Ensure sound is stopped before the next beat
            next_metronome_time += beat_interval  # Schedule next metronome beep

        # Refresh the window
        win.flip()

    print("Pulsating circle with metronome complete.")
    return pulsation_data

# Function for Image Description Task
def image_description_task(clock, duration, image_files):
    description_data = []
    end_time = clock.getTime() + duration
    image_index = 0  # Start with the first image

    print("Starting Image Description Task...")
    while clock.getTime() < end_time:
        # Load the current image
        current_image = image_files[image_index]
        image_stim = visual.ImageStim(win, image=os.path.join(image_folder, current_image), pos=(0, 0), size=(600, 600))

        # Draw the image
        image_stim.draw()
        win.flip()

        # Wait for participant input
        keys = event.waitKeys(keyList=['right', 'escape'], timeStamped=clock)

        # Handle key presses
        for key, timestamp in keys:
            if key == 'right':
                # Record the description event
                description_data.append({
                    'event': 'image_description',
                    'image': current_image,
                    'timestamp': timestamp
                })

                # Move to the next image
                image_index = (image_index + 1) % len(image_files)  # Loop to the start if at the end
            elif key == 'escape':
                win.close()
                core.quit()

    print("Image Description Task complete.")
    return description_data

# Phase 1: Tap to a blank screen with fixation cross
instruction_text.draw()
win.flip()
event.waitKeys(keyList=['space'])  # Wait for participant to press 'space' to start
print("Starting Phase 1: Tapping")
tapping_data = record_tapping(clock, duration, task_name="first_tapping")

# Pause Phase: Instruction for next phase
pause_text.draw()
win.flip()
core.wait(5)  # Wait 5 seconds

# Phase 2: Pulsating Circle or Metronome
print("Starting Phase 2: Pulsating Circle or Metronome")
pulsation_data = pulsating_circle(clock, duration=duration, metronome=metronome, include_metronome=(task_type in ["Metronome", "Both"]))

# Pause Phase 2: Instruction for next phase
pause2_text.draw()
win.flip()
core.wait(5)  # Wait 5 seconds

# Phase 3: Image Description Task
print("Starting Phase 3: Image Description Task")
description_data = image_description_task(clock, image_task_duration, image_files)

# Phase 4: Second tapping task with fixation cross
print("Starting Phase 4: Replicating the Rhythm")
instruction2_text.draw()
win.flip()
event.waitKeys(keyList=['space'])  # Wait for participant to press 'space' to start
second_tapping_data = record_tapping(clock, duration, task_name="second_tapping")

# End Message
end_text.draw()
win.flip()
core.wait(5)  # Show end message for 5 seconds

# Save Data
output_filename = f"participant_{participant_id}_data.csv"
with open(output_filename, mode='w', newline='') as file:
    fieldnames = ['event', 'image', 'timestamp', 'task_type', 'frequency', 'participant_age', 'musical_experience']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for data in tapping_data + pulsation_data + description_data + second_tapping_data:
        data['task_type'] = task_type #Add type of stimuli used
        data['frequency'] = frequency_choice #Add frequency of pulsation
        data['participant_age'] = participant_age  # Add participant age to each row
        data['musical_experience'] = musical_experience  # Add musical experience to each row
        writer.writerow(data)


# Close the window
win.close()
core.quit()
