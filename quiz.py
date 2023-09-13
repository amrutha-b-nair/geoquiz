import csv
from tkinter import *
from PIL import Image, ImageTk

# Read the CSV file
def read_csv(filename):
    questions = []
    alt_names = []
    with open(filename, 'r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            questions.append(row['Image_path'])
            alt_names.append(row['Other names'])
    return questions, alt_names

# Initialize the quiz
def start_quiz():
    global current_question, score
    current_question = 0
    score = 0
    result_label.place_forget()
    start_button.place_forget()
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
    if current_question < len(questions):
        image_path = questions[current_question]
        img = Image.open(image_path)
        width, height = img.size
        to_resize = float(400/max(width,height))
        img = img.resize((int(width*to_resize), int(height*to_resize)), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        image_label.config(image=photo)
        image_label.image = photo

        answer_entry.delete(0, END)
    else:
        result_label.config(text=f"Your Score: {score}/{len(questions)}")



# Check the user's answer
def check_answer():
    global current_question, score
    user_answer = answer_entry.get()
    if user_answer.lower() in alt_names[current_question].lower():
        score += 1
    current_question += 1
    display_question()
    update_score_label()


def update_score_label():
    score_label.config(text=f"Score: {score}/{len(questions)}")

def finish_quiz():
    result_label.place(relx=0.5, rely=0.4, anchor=CENTER)
    start_button.place(relx=0.5, rely=0.5, anchor=CENTER)
    result_label.config(text=f"Your Score: {score}/{len(questions)}")
    image_label.pack_forget()
    answer_label.pack_forget()
    submit_button.pack_forget()
    answer_entry.pack_forget()
    finish_button.pack_forget()
    score_label.pack_forget()
    

# Load questions and answers from CSV
questions, alt_names = read_csv('selected_names.csv')

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


answer_entry = Entry(frame2)


submit_button = Button(frame3, text="Submit", command=check_answer)


start_button = Button(root, text="Start Quiz", command=start_quiz)
start_button.place(relx=0.5, rely=0.5, anchor=CENTER)
# start_button.pack()

finish_button = Button(frame3, text="Finish Quiz", command=finish_quiz)

result_label = Label(root, text="")
# result_label.pack()

score_label = Label(frame1, text="")


root.mainloop()
