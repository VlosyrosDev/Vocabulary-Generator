import json
import os
import datetime
import time
from google import genai
import customtkinter as ctk
import threading
from xhtml2pdf import pisa


API_KEY=""
API_KEY_FILE = "config.json"
FORMAT="PDF"



def word_html_section(word_data):
    
    word = word_data['Word']
    definition = word_data['Definition']
    function = word_data['Function']
    examples = word_data['Examples']
    examples.append("N/A")
    examples.append("N/A")
    synonyms = word_data['Synonyms']
    antonyms = word_data['Antonyms']
    derivatives = word_data['Derivatives']
    html_section = f"""
    <tr>
            <td class="main-word">{word.capitalize()}</td>
            <td class="function">{function.capitalize()}</td>
            <td>
                <p class="definition">{definition.capitalize()}</p>
                <p class="examples">
                    -> {examples[0]}<br>
                    -> {examples[1]}
                </p>
                <p class="synonyms-antonyms">
                    <b>Synonyms:</b> {", ".join(synonyms)}<br>
                    <b>Antonyms:</b> {", ".join(antonyms)}
                </p>
    """

    for d in derivatives:
        html_section += derivative_html_section(d)

    html_section += """</td>
        </tr>"""

    return html_section

def derivative_html_section(data):
    word = data["Word"]
    definition = data['Definition']
    part_of_speech = data['Function']
    examples = data['Examples']
    html_derivative_full = f"""
        <p class="derivatives">
                    <b>{word.capitalize()} ({part_of_speech.capitalize()}):</b>
                    <span class="definition">{definition.capitalize()}</span><br>
                
        """
    if examples:
        for e in examples:
            html_derivative_full += f"""<span class="examples">-> {e}</span><br>"""

    html_derivative_full += "</p>"
    return html_derivative_full

def ask_google(word):
    for attempt in range(5):
        try:
            prompt = """For the word "{word}", return a JSON object with the following fields:

                - "Word": the word being analysed
                - "Function": one of "noun", "verb", "adjective", or "adverb"
                - "Definition": a clear, simple English definition
                - "Examples": a list of 2 complete sentences using the word naturally
                - "Synonyms": a list of at least 2 similar words
                - "Antonyms": a list of at least 2 opposite words
                - "Derivatives": a list of derivative words in different parts of speech (noun, verb, adjective, or adverb). Each item must be an object with:
                    - "Word": the derivative word
                    - "Function": one of "noun", "verb", "adjective", or "adverb"
                    - "Definition": a clear, simple English definition
                    - "Examples": a list of 2 complete sentences using the word naturally

                Requirements:
                - Do not repeat the original word in Derivatives unless it serves a different function.
                - Include at least 2 derivative words if possible.
                - Output only valid and complete JSON.
                - Give only the JSON immediately with no preamble.
                - Always enclose your lists with [] properly.
                - Use British spelling.

                Use this JSON schema:

                        {
                  "type": "object",
                  "properties": {
                    "Word": {
                      "type": "string"
                    },
                    "Function": {
                      "type": "string",
                      "enum": [
                        "Noun",
                        "Verb",
                        "Adjective",
                        "Adverb"
                      ]
                    },
                    "Definition": {
                      "type": "string"
                    },
                    "Examples": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "Synonyms": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "Antonyms": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      }
                    },
                    "Derivatives": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "Word": {
                            "type": "string"
                          },
                          "Function": {
                            "type": "string",
                            "enum": [
                              "Noun",
                              "Verb",
                              "Adjective",
                              "Adverb"
                            ]
                          },
                          "Definition": {
                            "type": "string"
                          },
                          "Examples": {
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          }
                        },
                        "required": [
                          "Word",
                          "Function",
                          "Definition",
                          "Examples"
                        ]
                      }
                    }
                  },
                  "required": [
                    "Word",
                    "Function",
                    "Definition",
                    "Examples",
                    "Synonyms",
                    "Antonyms",
                    "Derivatives"
                  ]
                }
                """
            prompt = prompt.replace("{word}", word)
            client = genai.Client(api_key=f"{API_KEY}")
            response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                )
            cleaned_response = response.text.lstrip('json ').strip("`")
            cleaned_response = cleaned_response.replace("json", "")
            cleaned_response = json.loads(cleaned_response)
            return cleaned_response
        except json.JSONDecodeError:
            print(f"Attempt {attempt + 1}: Invalid JSON format.")
            print(cleaned_response)

        except Exception as e:
            print(f"Attempt {attempt + 1}: Error occurred:", e)

        # Optional delay before retrying
        time.sleep(3)
    print("Failed to retrieve valid JSON after 5 attempts.")
    return None



def generate_html_from_words(words):
    progress_bar.pack(pady=5)
    api_enter_button.configure(state="disabled")
    generate_button.configure(state="disabled")
    format_selector.configure(state="disabled")
    html_end = """
            </table>
        </body>
        </html>
        """

    html_content = """
    <html>
    <head>
        <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid black; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .main-word { color: red; font-weight: bold; }
            .function { color: blue; }
            .definition { color: green; }
            .examples { color: purple; }
            .synonyms-antonyms { color: orange; }
            .derivatives { color: brown; }
        </style>
    </head>
    <body>
        <table>
            <tr>
                <th style="width: 100px;">Word</th>
                <th style="width: 80px;">Function</th>
                <th style="width: 400px;">Main Content</th>
            </tr>
     """
    counter = 1
    for word in words:
        start_time = time.time()
        word.capitalize()
        status_label.configure(text=f"Processing {word.capitalize()} ({counter}/{len(words)})")
        response = ask_google(word)
        if response != None:
            html_content += word_html_section(response)
        elapsed = time.time() - start_time
        time_to_wait = max(0, 4.1 - elapsed)
        counter += 1
        time.sleep(time_to_wait)
        os.system('cls' if os.name == 'nt' else 'clear')
    html_content += html_end
    api_enter_button.configure(state="normal")
    generate_button.configure(state="normal")
    format_selector.configure(state="normal")
    return html_content

def generate_vocab():
    if not API_KEY:
        feedback_label.configure(text="Please enter an API key.", text_color="#ffaa00")
        return
    words = text_input.get("1.0", "end-1c").strip().split("\n")
    if len(words) == 1:
        feedback_label.configure(text="Please enter some words (Minimum: 2).", text_color="#ffaa00")
        return
    progress_bar.configure(mode="indeterminate")
    progress_bar.start()
    
    def task():
        html = generate_html_from_words(words)
        if FORMAT == "HTML":
            output_file = f"PatherVocab_{datetime.datetime.now().strftime('%Y-%m-%d')}_{words[0].capitalize()}-{words[len(words) - 1].capitalize()}.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)
            progress_bar.stop()
            status_label.configure(text=f"Done! Saved {len(words)} words as {output_file}")
        elif FORMAT=="PDF":
            output_file = f"PatherVocab_{datetime.datetime.now().strftime('%Y-%m-%d')}_{words[0].capitalize()}-{words[len(words) - 1].capitalize()}.pdf"
            with open(output_file, 'wb') as result_file:
                pisa.CreatePDF(html, dest=result_file)
            progress_bar.stop()
            status_label.configure(text=f"Done! Saved {len(words)} words as {output_file}")

        progress_bar.pack_forget()

    threading.Thread(target=task).start()

app = ctk.CTk()
app.geometry("700x700")
app.title("Vocabulary Generator")
app.configure(fg_color="#121212")
app.iconbitmap("icon.ico")
ctk.set_appearance_mode("dark")

def load_api_key():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as file:
            data = json.load(file)
            return data.get("API_KEY", "")
    return ""

def save_api_key(api_key):
    with open(API_KEY_FILE, "w") as file:
        json.dump({"API_KEY": api_key}, file)

def on_format_change(choice):
    global FORMAT
    FORMAT = choice
    generate_button.configure(text=f"Generate {FORMAT}")


saved_api_key = load_api_key()

font_title = ctk.CTkFont(family="Courier New", size=16)
font_body = ctk.CTkFont(family="Courier New", size=14)

def apply_api_key():
    api_key = api_entry.get().strip()
    if api_key:
        global API_KEY
        API_KEY = api_key
        save_api_key(api_key)
        feedback_label.configure(text="API key saved successfully.", text_color="#00ff88")
    else:
        feedback_label.configure(text="Please enter a valid API key.", text_color="#ffaa00")

if saved_api_key:
    # Label
    api_label = ctk.CTkLabel(app, text="Enter your API Key (Using saved one):", text_color="#00ff88", font=font_body)
    api_label.pack(pady=(20, 5))

    # Entry field
    api_entry = ctk.CTkEntry(app, width=350, placeholder_text=f"{saved_api_key}", justify="center", text_color="#00ff88", font=font_body)
    api_entry.pack(pady=(0, 10))
    API_KEY=saved_api_key
else:
     # Label
    api_label = ctk.CTkLabel(app, text="Enter your API Key:", text_color="#00ff88", font=font_body)
    api_label.pack(pady=(20, 5))

    # Entry field
    api_entry = ctk.CTkEntry(app, width=350, placeholder_text="Paste your API key", justify="center", text_color="#00ff88", font=font_body)
    api_entry.pack(pady=(0, 10))

api_enter_button = ctk.CTkButton(app, text="Enter", font=font_body, fg_color="#00ff88",text_color="#1e1e1e", hover_color="#22ffaa", command=apply_api_key)
api_enter_button.pack(pady=5)

# Feedback label
feedback_label = ctk.CTkLabel(app, text="", text_color="#00ff88", font=font_body)
feedback_label.pack(pady=(10, 10))

instruction_label = ctk.CTkLabel(app, text="Enter one word per line:", text_color="#00ff88", font=font_title)
instruction_label.pack()

text_input = ctk.CTkTextbox(app, width=500, height=300, text_color="#00ff88", font=font_body)
text_input.configure(fg_color="#1e1e1e", border_color="#00ff88", border_width=1)
text_input.pack(padx=10, pady=10)

generate_button = ctk.CTkButton(app, text="Generate PDF", font=font_body, fg_color="#00ff88",text_color="#1e1e1e", hover_color="#22ffaa", command=generate_vocab)
generate_button.pack(pady=5)

# Dropdown menu for selecting output format
format_selector = ctk.CTkOptionMenu(app, values=["PDF", "HTML"], command=on_format_change, fg_color="#00ff88",text_color="#1e1e1e", button_color="#00ff88", button_hover_color="#22ffaa", dropdown_fg_color="#00ff88", dropdown_hover_color="#00e67a", font=font_body, dropdown_font=font_body, dropdown_text_color="#1e1e1e", width=70)
format_selector.set("PDF")  # Default value
format_selector.pack(pady=5)

progress_bar = ctk.CTkProgressBar(app, progress_color="#66ccff")

status_label = ctk.CTkLabel(app, text="", text_color="#66ccff", font=font_body)
status_label.pack(pady=(10, 0))

app.mainloop()