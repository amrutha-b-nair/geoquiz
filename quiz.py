import csv
from tkinter import *
from PIL import Image, ImageTk
import random

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
    all_country.place_forget()
    ten_countries.place_forget()
    score_label.pack(pady=10)
    image_label.pack(pady=10)
    answer_label.pack(side = LEFT, padx = 5)
    answer_entry.pack(side = RIGHT)
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
        image_path = image_answers[current_question][0]
        img = Image.open(image_path)
        width, height = img.size
        to_resize = float(400/max(width,height))
        img = img.resize((int(width*to_resize), int(height*to_resize)), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        image_label.config(image=photo)
        image_label.image = photo

        answer_entry.delete(0, END)
    else:
        result_label.config(text=f"Your Score: {score}/{len(image_answers)}")
        finish_quiz()



# Check the user's answer
def check_answer():
    global current_question, score, answer_display
    user_answer = answer_entry.get()
    time_to_wait = 200
    if user_answer.lower() in image_answers[current_question][1]:
        score += 1
        submit_button.config(bg="green")
        root.update()
        root.after(500, reset_button_color)
    else:
        submit_button.config(bg="red")
        if answer_display:
            correct_answer_label.config(text=f"Correct Answer: {image_answers[current_question][2]}")
            print(image_answers[current_question][2])
            correct_answer_label.place_forget()
            time_to_wait = 1000
        root.update()
        root.after(500, reset_button_color)
    current_question += 1
    root.after(time_to_wait,display_question())
    update_score_label()



def reset_button_color():
    submit_button.config(bg="light gray")



def update_score_label():
    score_label.config(text=f"Score: {score}/{len(image_answers)}")

def finish_quiz():
    result_label.place(relx=0.5, rely=0.4, anchor=CENTER)
    start_button.place(relx=0.5, rely=0.5, anchor=CENTER)
    result_label.config(text=f"Your Score: {score}/{len(image_answers)}")
    image_label.pack_forget()
    answer_label.pack_forget()
    submit_button.pack_forget()
    answer_entry.pack_forget()
    finish_button.pack_forget()
    score_label.pack_forget()
    
    
def on_enter_key(event):
    # Check if any button is currently in focus
    focused_widget = root.focus_get()
    if isinstance(focused_widget, Button):
        # If a button is in focus, simulate its click
        button_name = focused_widget.cget("text")
        buttons[button_name].invoke()
    elif submit_button.winfo_ismapped():
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
    image_answers = random.sample(image_answers_all, k)
    start_quiz()

def show_answer():
    global answer_display
    show_correct_answer.place_forget()
    no_correct_answer.place_forget()
    all_country.place(relx=0.5, rely=0.5, anchor=CENTER)
    ten_countries.place(relx=0.5, rely=0.4, anchor=CENTER)
    answer_display = True


def no_show_answer():
    global answer_display
    show_correct_answer.place_forget()
    no_correct_answer.place_forget()
    correct_answer_label.pack_forget()
    all_country.place(relx=0.5, rely=0.5, anchor=CENTER)
    ten_countries.place(relx=0.5, rely=0.4, anchor=CENTER)
    answer_display = False

# Load questions and answers from CSV
image_answers_all = read_csv('selected_names.csv')
# Create the quiz GUI
root = Tk()
root.title("Quiz")
root.geometry("600x700")

frame1 = Frame(root)
frame1.pack(pady=10)  # Add vertical space

frame2 = Frame(root)
frame2.pack(pady=10) 

frame3 = Frame(root)
frame3.pack(pady=10) 

image_label = Label(frame1)


answer_label = Label(frame2, text="Your Answer:")
correct_answer_label = Label(frame3, text="")
correct_answer_label.pack()

answer_entry = Entry(frame2)


submit_button = Button(frame3, text="Submit", command=check_answer)
submit_button.bind("<Return>", lambda event=None: submit_button.invoke())


start_button = Button(root, text="Start Quiz", command=select_quiz)
start_button.place(relx=0.5, rely=0.5, anchor=CENTER)
# start_button.pack()


show_correct_answer = Button(root, text="Show correct answer", command=show_answer)
no_correct_answer = Button(root, text="Don't show answer", command=no_show_answer)

finish_button = Button(frame3, text="Finish Quiz", command=finish_quiz)


result_label = Label(root, text="")
# result_label.pack()
all_country = Button(root, text="All countries", command=lambda: quiz_type(len(image_answers)))

ten_countries = Button(root, text="10 countries", command=lambda: quiz_type(10))


buttons = {"Finish Quiz": finish_button, "Start Quiz": start_button, 
           "Submit": submit_button, "10 countries": ten_countries, 
           "All countries": all_country, "Show correct answer": show_correct_answer,
           "Don't show answer": no_correct_answer}

score_label = Label(frame1, text="")
root.bind("<Return>", on_enter_key)

root.mainloop()

