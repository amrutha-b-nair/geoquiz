import csv
from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import pygame
from fuzzywuzzy import fuzz
import importlib
from tkinter import simpledialog


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
    if default_10:
        quiz_type(10)
    show_correct_answer.pack_forget()
    random_button.pack_forget()
    order_button.pack_forget()
    all_country.pack_forget()
    select_number.pack_forget()
    select_number_label.pack_forget()
    wrong_label.pack_forget()
    order_label.pack_forget()
    enter_manually.pack_forget()
    start.pack_forget()
    result_label.place_forget()
    start_button.place_forget()
    line1.destroy()
    line2.destroy()
    line3.destroy()
    label_empty.pack_forget()
    score_label.pack(pady=30)
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
        to_resize = float(500/max(width,height))
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



def quiz_type(k):
    global image_answers, default_10
    default_10 = False
    if order_var.get() == "Increasing difficulty":
        image_answers = image_answers_all[:k]
    elif order_var.get() == "Random order":
        image_answers = random.sample(image_answers_all, k)
    select_number.config(text= "Selected number of countries:" + str(k))
    

def show_answer():
    global answer_display
    if show_answers_var.get():
        answer_display = True
    else:
        answer_display = False


def quiz_length():
    user_input = simpledialog.askstring("Input", "Enter the number of countries in quiz:")
    try:
        n = int(user_input)
        select_number.config(text= "Number of countries:" + str(n))
        quiz_type(n)
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid integer")

def create_horizontal_line():
    line = Frame(root, height=2, bd=1, relief=SUNKEN)
    line.pack(fill=X, pady=5)
    return line


def settings():
    global line1, line2, line3
    result_label.place_forget()
    start_button.place_forget()
    label_empty.pack(pady=30)
    wrong_label.pack()
    show_correct_answer.pack(pady=10)
    line1 = create_horizontal_line()

    order_label.pack(pady=10)
    random_button.pack()
    order_button.pack(pady=10)
    line2 = create_horizontal_line()

    select_number_label.pack()

    all_country.pack()
    enter_manually.pack(pady=10)
    select_number.pack()
    line3 = create_horizontal_line()

    start.pack(pady=10)




pygame.init()

with importlib.resources.path(__package__, 'sound') as sound_folder:
    correct_sound = pygame.mixer.Sound(str(sound_folder / 'correct.wav'))
    wrong_sound = pygame.mixer.Sound(str(sound_folder /'wrong.mp3')) 

# Load questions and answers from CSV
with importlib.resources.path(__package__, 'csv') as csv_folder:
    image_answers_all = read_csv(str(csv_folder /'selected_names.csv'))

root = Tk()
root.title("Quiz")
root.geometry("700x800")

frame1 = Frame(root)
frame2 = Frame(root)
frame3 = Frame(root)

image_label = Label(frame1)


answer_label = Label(frame2, text="Your Answer:",font=("Helvetica", 15),)
correct_answer_label = Label(frame3, font=("Helvetica", 15),text="")
correct_answer_label.pack()

answer_entry = Entry(frame2,font=("Helvetica", 15))


submit_button = Button(frame3, text="Submit",font=("Helvetica", 15), command=check_answer)


start_button = Button(root, text="Start Quiz",font=("Helvetica", 20), command=settings)
start_button.place(relx=0.5, rely=0.5, anchor=CENTER)

show_answers_var = BooleanVar()
wrong_label = Label(root, text="To see correct answer if you make a mistake.",font=("Ariel", 15, "italic"))
show_correct_answer = Checkbutton(root, text="Show Answers", variable=show_answers_var,font=("Helvetica", 15), command=show_answer)
show_answers_var.set(True)


order_var = StringVar()
order_var.set("Increasing difficulty")
order_label = Label(root, text="Choose if the countries should appear in random order or in increasing difficulty",font=("Ariel", 15, "italic"))
random_button = Radiobutton(root, text="Random order",font=("Helvetica", 15), variable=order_var, value="Random order")
order_button = Radiobutton(root, text="Increasing difficulty",font=("Helvetica", 15), variable=order_var, value="Increasing difficulty")


default_10 = True
select_number_label = Label(root, text="Select the number of countries (default: 10):",font=("Ariel", 15, "italic"))
select_number = Label(root, text="Selected number of countries: 10",font=("Helvetica", 15))
all_country = Button(root, text="All countries",font=("Helvetica", 15), command=lambda: quiz_type(len(image_answers_all)))
enter_manually = Button(root, text="Enter the number of Countries",font=("Helvetica", 15), command= quiz_length)




start = Button(root, text="Start",font=("Helvetica", 20), command=start_quiz)


finish_button = Button(frame3, text="Finish Quiz",font=("Helvetica", 15), command=finish_quiz)


result_label = Label(root,font=("Helvetica", 15), text="")






buttons = {"Finish Quiz": finish_button, "Start Quiz": start_button, 
           "Submit": submit_button, 
           "All countries": all_country, "Show Answers": show_correct_answer,
           "Random order":random_button, "Start":start,
           "Increasing difficulty": order_button}

score_label = Label(frame1,font=("Helvetica", 15), text="")
label_empty = Label(root, text="")

root.bind("<Return>", on_enter_key)

root.mainloop()

