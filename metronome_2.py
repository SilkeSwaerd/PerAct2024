from psychopy import visual, core, event, gui, prefs
import csv
import os
import numpy as np

prefs.hardware['audioLib'] = ['pygame']  # or ['sounddevice', 'pyo']
from psychopy import sound

# Try initializing sound
try:
    metronome = sound.Sound(value='A', secs=0.1)
    metronome.play()
except Exception as e:
    print(f"Error initializing metronome sound: {e}")


# Task Selection Dialog
task_dialog = gui.Dlg(title="Task Selection")
task_dialog.addField("Choose task type:", choices=["Visual Pulsation", "Metronome", "Both"])
task_dialog.show()

if task_dialog.OK:
    task_type = task_dialog.data[0]
else:
    core.quit()  # Exit if dialog is canceled

# Participant Info Dialog
participant_dialog = gui.Dlg(title="Participant Info")
participant_dialog.addField("Participant ID:")
participant_dialog.show()

if participant_dialog.OK:
    participant_id = participant_dialog.data[0]  # Get the participant ID from the dialog
else:
    core.quit()  # Exit if dialog is canceled

# Define fullscreen window
win = visual.Window(color=[-1, -1, -1], units="pix", fullscr=True)

# Define text stimuli
instruction_text = visual.TextStim(win, text="Tap the spacebar to the rhythm you feel.\n\nPress 'space' to start.", 
                                   color="white", height=30, wrapWidth=800)
pause_text = visual.TextStim(win, text="Get ready!\n\nWatch the screen and follow the rhythm without tapping.",
                             color="white", height=30, wrapWidth=800)
pause2_text = visual.TextStim(win, text="Get ready!\n\nNow choose one of these two images.",
                              color="white", height=30, wrapWidth=800)   
instruction_text = visual.TextStim(win, text="Now, please try to replicate the rhythm you tapped earlier.\n\nPress 'space' to start.", 
                                   color="white", height=30, wrapWidth=800)                            

end_text = visual.TextStim(win, text="Thank you! The experiment is over.", color="white", height=30)

# Define the pulsating circle
circle = visual.Circle(win, radius=80, fillColor='white', lineColor='white')

# Set up timing parameters
pulsation_interval = 0.6  # 600 ms between pulsations
duration = 20  # Duration of each phase in seconds
image_task_duration = 30  # Time allocated for the image task (in seconds)

# Load image file names
image_folder = "./"  # Images are in the same folder as the program
image_files = [f for f in os.listdir(image_folder) if f.endswith('.jpg')]

# Initialize clock
clock = core.Clock()

# Function to record key presses (tapping)
def record_tapping(clock, duration, task_name):
    tapping_data = []
    end_time = clock.getTime() + duration

    while clock.getTime() < end_time:
        # Check for key presses
        keys = event.getKeys(timeStamped=clock)
        for key, timestamp in keys:
            if key == 'space':
                tapping_data.append({'event': f'{task_name}_keypress', 'timestamp': timestamp})
            elif key == 'escape':  # Exit on 'escape' key
                win.close()
                core.quit()
    return tapping_data

# Function to show the pulsating circle
def pulsating_circle(clock, metronome, duration, include_metronome=False):
    pulsation_data = []
    end_time = clock.getTime() + duration
    next_pulsation_time = clock.getTime()

    while clock.getTime() < end_time:
        t = clock.getTime()

        if t >= next_pulsation_time:
            if task_type in ["Visual Pulsation", "Both"]:
                circle.draw()
            if task_type in ["Metronome", "Both"]:
                metronome.play()  # Play the metronome sound
            win.flip()
            pulsation_data.append({'event': 'pulsation', 'timestamp': t})
            next_pulsation_time += pulsation_interval
        else:
            win.flip()
    return pulsation_data

# Function for Image Choice Task
def image_choice_task(clock, duration, image_files):
    choice_data = []
    end_time = clock.getTime() + duration

    while clock.getTime() < end_time:
        # Randomly pick two different images
        img1, img2 = np.random.choice(image_files, size=2, replace=False)

        # Create ImageStim objects for the left and right images
        image_left = visual.ImageStim(win, image=os.path.join(image_folder, img1), pos=(-200, 0), size=(300, 300))
        image_right = visual.ImageStim(win, image=os.path.join(image_folder, img2), pos=(200, 0), size=(300, 300))

        # Draw images and flip the window
        image_left.draw()
        image_right.draw()
        win.flip()

        # Wait for participant's choice
        keys = event.waitKeys(keyList=['left', 'right', 'escape'], timeStamped=clock)

        # Record the choice
        for key, timestamp in keys:
            if key in ['left', 'right']:
                choice_data.append({
                    'event': 'choice',
                    'choice': key,
                    'image_left': img1,
                    'image_right': img2,
                    'timestamp': timestamp
                })
                break  # Proceed to the next pair of images
            elif key == 'escape':  # Exit experiment
                win.close()
                core.quit()

    return choice_data

# Phase 1: Tap to a blank screen
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

# Phase 3: Image Choice Task
print("Starting Phase 3: Image Choice Task")
choice_data = image_choice_task(clock, image_task_duration, image_files)

# Phase 4: Second tapping task
print("Starting Phase 4: Replicating the Rhythm")

# Instruction for second tapping task
instruction_text.draw()
win.flip()
event.waitKeys(keyList=['space'])  # Wait for participant to press 'space' to start

# Record second tapping task
clock.reset()
second_tapping_data = record_tapping(clock, duration, task_name="second_tapping")

# End Message
end_text.draw()
win.flip()
core.wait(5)  # Show end message for 5 seconds

# Save Data
output_filename = f"participant_{participant_id}_data.csv"
with open(output_filename, mode='w', newline='') as file:
    fieldnames = ['event', 'choice', 'image_left', 'image_right', 'timestamp']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(tapping_data + pulsation_data + choice_data + second_tapping_data)  # Combine all datasets

# Close the window
win.close()
core.quit()
