import csv
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import pygame
from fuzzywuzzy import fuzz
import importlib

# Read the CSV file
def read_csv(filename):

    image_answers = []
    with open(filename, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            image_answers.append([row['Image_path'],  row['Other names'].lower().split(','),
                                  row['Country']])
    return image_answers

# Initialize the quiz
def start_quiz():
    global current_question, score
    current_question = 0
    score = 0
    result_label.place_forget()
    start_button.place_forget()
    all_country.pack_forget()
    ten_countries.pack_forget()
    enter_number.pack_forget()
    number_countries.pack_forget()
    number_submit.pack_forget()
    center_frame.pack_forget()
    button_frame.pack_forget()
    row_frame.pack_forget()
    score_label.pack(pady=10)
    frame1.pack(pady=10) 
    image_label.pack(pady=10)
    frame2.pack(pady=10)
    answer_label.pack(side = LEFT, padx = 5)
    answer_entry.pack(side = RIGHT)
    answer_entry.focus_set()
    frame3.pack(pady=10) 
    submit_button.pack(pady=10)
    finish_button.pack()
    update_score_label()
    display_question()
    

# Display the current question
def display_question():
    global current_question, score
    correct_answer_label.config(text="")
    if current_question < len(image_answers):
        # submit_button.config(bg="light gray")
        image_name = image_answers[current_question][0]
        with importlib.resources.path(__package__, 'images_noaxis') as image_folder:
            image_path = str(image_folder/image_name)
        img = Image.open(image_path)
        width, height = img.size
        to_resize = float(400/max(width,height))
        img = img.resize((int(width*to_resize), int(height*to_resize)), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        image_label.config(image=photo)
        image_label.image = photo
        answer_entry.delete(0, END)
    else:
        finish_button.pack_forget()
        result_label.config(text=f"Your Score: {score}/{len(image_answers)}")
        finish_quiz()



# Check the user's answer
def check_answer():
    global current_question, score, answer_display
    user_answer = answer_entry.get()
    time_to_wait = 200
    if user_answer.lower() in image_answers[current_question][1]:
        score += 1
        correct() 
    else:
        if check_similarity(user_answer):
            score += 1
            correct()
        else:
            submit_button.config(bg="red")
            wrong_sound.play()
            if answer_display:
                correct_answer_label.config(text=f"Correct Answer: {image_answers[current_question][2]}")
                correct_answer_label.place_forget()
                time_to_wait = 1000
            root.update()
            root.after(500, reset_button_color)
    current_question += 1
    root.after(time_to_wait,display_question())
    update_score_label()

def check_similarity(user_answer):
    global current_question
    similarity = []
    for answer in image_answers[current_question][1]:
        similarity_ratio = fuzz.ratio(user_answer, answer)
        similarity.append(similarity_ratio)
    similarity_score = max(similarity)
    if similarity_score > 85:
        return True

def correct():
    correct_sound.play()
    submit_button.config(bg="green")
    root.update()
    root.after(500, reset_button_color)

def reset_button_color():
    submit_button.config(bg="light gray")



def update_score_label():
    score_label.config(text=f"Score: {score}/{len(image_answers)}")

def finish_quiz():
    result_label.place(relx=0.5, rely=0.4, anchor=CENTER)
    start_button.place(relx=0.5, rely=0.5, anchor=CENTER)
    result_label.config(text=f"Your Score: {score}/{len(image_answers)}")
    image_label.pack_forget()
    frame1.pack_forget()
    answer_label.pack_forget()
    frame2.pack_forget()
    submit_button.pack_forget()
    frame3.pack_forget()
    answer_entry.pack_forget()
    root.focus_set()
    finish_button.pack_forget()
    score_label.pack_forget()
    
    
def on_enter_key(event):
    # Check if any button is currently in focus
    focused_widget = root.focus_get()
    if isinstance(focused_widget, Button) and focused_widget.winfo_ismapped():
        # If a button is in focus, simulate its click
        button_name = focused_widget.cget("text")
        buttons[button_name].invoke()
    elif submit_button.winfo_ismapped() and (focused_widget == answer_entry):
        # If no button is in focus, simulate the "Submit" button click
        submit_button.invoke()
    elif start_button.winfo_ismapped():
        start_button.invoke()

        

def select_quiz():
    result_label.place_forget()
    start_button.place_forget()
    show_correct_answer.place(relx=0.5, rely=0.5, anchor=CENTER)
    no_correct_answer.place(relx=0.5, rely=0.4, anchor=CENTER)
    

def quiz_type(k):
    global image_answers
    if order == True:
        image_answers = image_answers_all[:k]
    elif order == False:
        image_answers = random.sample(image_answers_all, k)
    start_quiz()

def show_answer(k):
    global answer_display
    show_correct_answer.place_forget()
    no_correct_answer.place_forget()
    random_button.place(relx=0.5, rely=0.5, anchor=CENTER)
    order_button.place(relx=0.5, rely=0.4, anchor=CENTER)
    if k == True:
        answer_display = True
    elif k == False:
        answer_display = False
        correct_answer_label.place_forget()


def ordering(k):
    global order 
    order = k
    random_button.place_forget()
    order_button.place_forget()
    center_frame.pack(expand=True, fill=BOTH)
    button_frame.pack()
    all_country.pack(padx=10, pady=10)
    ten_countries.pack(padx=10, pady=10)
    row_frame.pack()
    enter_number.pack(side=LEFT, padx=10, pady=10)
    number_countries.pack(side=LEFT, padx=10, pady=10)
    number_submit.pack(side=LEFT, padx=10, pady=10)

def quiz_length():
    user_input = number_countries.get()
    try:
        n = int(user_input)
        quiz_type(n)
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid integer")

pygame.init()

with importlib.resources.path(__package__, 'sound') as sound_folder:
    correct_sound = pygame.mixer.Sound(str(sound_folder / 'correct.wav'))
    wrong_sound = pygame.mixer.Sound(str(sound_folder /'wrong.mp3')) 

# Load questions and answers from CSV
with importlib.resources.path(__package__, 'csv') as csv_folder:
    image_answers_all = read_csv(str(csv_folder /'selected_names.csv'))
# Create the quiz GUI
root = Tk()
root.title("Quiz")
root.geometry("600x700")

frame1 = Frame(root)
# frame1.pack(pady=10)  # Add vertical space

frame2 = Frame(root)
# frame2.pack(pady=10) 

frame3 = Frame(root)
# frame3.pack(pady=10) 

image_label = Label(frame1)


answer_label = Label(frame2, text="Your Answer:",font=("Helvetica", 15),)
correct_answer_label = Label(frame3, font=("Helvetica", 15),text="")
correct_answer_label.pack()

answer_entry = Entry(frame2,font=("Helvetica", 15))


submit_button = Button(frame3, text="Submit",font=("Helvetica", 15), command=check_answer)
# submit_button.bind("<Return>", lambda event=None: submit_button.invoke())


start_button = Button(root, text="Start Quiz",font=("Helvetica", 20), command=select_quiz)
start_button.place(relx=0.5, rely=0.5, anchor=CENTER)
# start_button.pack()


show_correct_answer = Button(root, text="Show correct answer",font=("Helvetica", 15), command=lambda: show_answer(True))
no_correct_answer = Button(root, text="Don't show answer", font=("Helvetica", 15), command=lambda: show_answer(False))

finish_button = Button(frame3, text="Finish Quiz",font=("Helvetica", 15), command=finish_quiz)


result_label = Label(root,font=("Helvetica", 15), text="")
# result_label.pack()


center_frame = Frame(root)
button_frame = Frame(center_frame)
row_frame = Frame(center_frame)
# button_frame.pack()
# row_frame.pack()
# center_frame.pack(expand=True, fill=BOTH)

all_country = Button(button_frame, text="All countries",font=("Helvetica", 15), command=lambda: quiz_type(len(image_answers_all)))
ten_countries = Button(button_frame, text="10 countries",font=("Helvetica", 15), command=lambda: quiz_type(10))
number_countries = Entry(row_frame,font=("Helvetica", 15))
number_submit = Button(row_frame, text="Go",font=("Helvetica", 15), command=lambda: quiz_length())
enter_number = Label(row_frame, text="Number of countries:",font=("Helvetica", 15),)

random_button = Button(root, text = "Random order", font=("Helvetica", 15), command = lambda: ordering(False))
order_button = Button(root, text = "Increasing difficulty", font=("Helvetica", 15), command = lambda: ordering(True))



# Create a frame for centering all widgets






buttons = {"Finish Quiz": finish_button, "Start Quiz": start_button, 
           "Submit": submit_button, "10 countries": ten_countries, 
           "All countries": all_country, "Show correct answer": show_correct_answer,
           "Don't show answer": no_correct_answer, "Random order":random_button,
           "Increasing difficulty": order_button, "Go": number_submit}

score_label = Label(frame1,font=("Helvetica", 15), text="")
root.bind("<Return>", on_enter_key)

root.mainloop()

