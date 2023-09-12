import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


# Define a list of quiz questions and answers, along with corresponding image file paths.
questions = [
    {
        "question": "Name the country",
        "answer": "France",
        "image_path": "/home/allu/quiz/sample_images/France.png",
    },
    {
        "question": "Name the country",
        "answer": "Spain",
        "image_path": "/home/allu/quiz/sample_images/Spain.png",
    },

]

# Define a function to check the user's answer.
def check_answer():
    user_answer = entry.get()
    correct_answer = questions[current_question]["answer"]

    if user_answer.lower() == correct_answer.lower():
        messagebox.showinfo("Correct", "Your answer is correct!")
    else:
        messagebox.showerror("Incorrect", f"Sorry, the correct answer is {correct_answer}.")

    next_question()

# Define a function to display the next question.
def next_question():
    global current_question
    current_question += 1

    if current_question < len(questions):
        display_question()
    else:
        messagebox.showinfo("Quiz Complete", "Congratulations! You have completed the quiz.")
        window.quit()

# Define a function to display the current question and image.
def display_question():
    question_label.config(text=questions[current_question]["question"])
    entry.delete(0, tk.END)
    
    # Load and display the image.
    image_path = questions[current_question]["image_path"]
    img = Image.open(image_path)
    img = img.resize((300, 200), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    image_label.config(image=photo)
    image_label.image = photo

# Create the main window.
window = tk.Tk()
window.title("Quiz")
window.geometry("400x300")

current_question = 0

# Create widgets for the question, image, and answer input.
question_label = tk.Label(window, text="", font=("Arial", 14))
question_label.pack(pady=10)

image_label = tk.Label(window)
image_label.pack()

entry = tk.Entry(window, font=("Arial", 12))
entry.pack(pady=10)

check_button = tk.Button(window, text="Check Answer", command=check_answer)
check_button.pack()

# Start the quiz with the first question.
display_question()

# Start the Tkinter main loop.
window.mainloop()
