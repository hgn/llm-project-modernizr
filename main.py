#!/usr/bin/env python3

import argparse
import os
import shutil
import time
import mimetypes
import textwrap
from openai import OpenAI
import toml
import json

MODEL = "gpt-4o"
client = OpenAI()
LOG_FILE_PATH = "/tmp/llm-project-modernizr.log"

# Load source code suffixes from the external TOML file
SOURCE_CODE_SUFFIXES = toml.load('assets/source-code-suffixes.toml')['suffixes']['suffixes']

def log_request(request_data):
    """Logs the request data to a log file."""
    with open(LOG_FILE_PATH, "a") as log_file:
        log_file.write(json.dumps(request_data, indent=2) + "\n\n")

def chat_completion_create(model, messages):
    """Wrapper function to log and call the original chat completion create method."""
    request_data = {
        "model": model,
        "messages": messages,
    }
    log_request(request_data)
    return client.chat.completions.create(
        model=model,
        messages=messages
    )

def load_prompt(analyzer_dir, stage):
    """Load the system and user prompts from the specified analyzer's TOML files."""
    toml_path = os.path.join(analyzer_dir, f'stage{stage}.toml')
    if not os.path.exists(toml_path):
        raise FileNotFoundError(f"TOML file not found: {toml_path}")
    
    prompts = toml.load(toml_path)
    system_prompt = prompts.get('system', {}).get('content', '')
    user_prompt = prompts.get('user', {}).get('content', '')
    return system_prompt, user_prompt

class ProjectAnalyzer:
    def __init__(self, project_path):
        print(f"Analyze project {project_path}")
        print(f"Model {MODEL}")
        self.project_path = project_path
        self.project_name = os.path.basename(os.path.normpath(project_path))
        self.output_dir = f"results-{self.project_name}"
        self.ignore_patterns = ['.git', '.gitignore']  # Always ignore the .git directory
        self.analyzers = self.discover_analyzers()

    def setup_output_directory(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

    def discover_analyzers(self):
        """Discover all analyzers by finding directories in the analyzer folder."""
        analyzer_root = 'analyzer'
        analyzers = []
        for analyzer_name in os.listdir(analyzer_root):
            analyzer_dir = os.path.join(analyzer_root, analyzer_name)
            if os.path.isdir(analyzer_dir):
                analyzers.append(analyzer_dir)
        return analyzers

    def load_gitignore(self):
        gitignore_path = os.path.join(self.project_path, '.gitignore')
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as gitignore_file:
                for line in gitignore_file:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.ignore_patterns.append(line)
            print("Loaded .gitignore patterns:", self.ignore_patterns)

    def should_ignore(self, path):
        for pattern in self.ignore_patterns:
            if pattern in path:
                return True
        if path.endswith(tuple(SOURCE_CODE_SUFFIXES)):
            return False
        return True

    def generate_tree_structure(self):
        print("Generate tree structure")
        tree_file_path = os.path.join(self.output_dir, "tree.txt")
        
        def build_tree(directory, prefix=''):
            items = sorted(os.listdir(directory))
            for index, item in enumerate(items):
                item_path = os.path.join(directory, item)

                if ".git" in item_path:
                    continue
                
                if index == len(items) - 1:
                    tree_file.write(f"{prefix}└── {item}\n")
                    new_prefix = f"{prefix}    "
                else:
                    tree_file.write(f"{prefix}├── {item}\n")
                    new_prefix = f"{prefix}│   "
                
                if os.path.isdir(item_path):
                    build_tree(item_path, new_prefix)
        
        with open(tree_file_path, "w") as tree_file:
            tree_file.write(f"{os.path.basename(self.project_path)}/\n")
            build_tree(self.project_path)

    def read_tree_file(self):
        tree_file_path = os.path.join(self.output_dir, "tree.txt")
        with open(tree_file_path, "r") as file:
            return file.read()

    def is_text_file(self, file_path):
        mimetype, _ = mimetypes.guess_type(file_path)
        if mimetype and mimetype.startswith('text'):
            return True
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            return True
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            return False

    def analyze_file_with_analyzer(self, analyzer_dir, file_path, relative_path, content, tree_structure):
        """Analyze a file using the specified analyzer."""
        analyzer_name = os.path.basename(analyzer_dir)
        system_prompt, user_prompt = load_prompt(analyzer_dir, 1)
        user_prompt = user_prompt.replace("{content}", content).replace("{tree_structure}", tree_structure).replace("{relative_path}", relative_path)

        response = chat_completion_create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        analysis = response.choices[0].message.content
        analysis = self.format_markdown(analysis)

        output_file_path = os.path.join(self.output_dir, f"{relative_path}-{analyzer_name}.md")
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, "w") as analysis_file:
            analysis_file.write(analysis)
        print(f'   wrote info to {output_file_path}')

    def analyze_file(self, file_path, relative_path):
        if not self.is_text_file(file_path):
            print(f"Skipping binary or non-text file: {file_path}")
            return

        if self.should_ignore(file_path):
            print(f"Skipping file based on ignore list: {file_path}")
            return

        print(f"Analyze file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        tree_structure = self.read_tree_file()

        for analyzer_dir in self.analyzers:
            analyzer_name = os.path.basename(analyzer_dir)
            print(f"  analyzing with {analyzer_name} analyzer")
            self.analyze_file_with_analyzer(analyzer_dir, file_path, relative_path, content, tree_structure)

    def format_markdown(self, content):
        lines = content.splitlines()
        formatted_lines = []

        for line in lines:
            if line.startswith("#"):
                formatted_lines.append("")  # Add a blank line before headers
                formatted_lines.append(line)
                formatted_lines.append("")  # Add a blank line after headers
            else:
                wrapped_lines = textwrap.wrap(line, width=80)
                formatted_lines.extend(wrapped_lines)

        return "\n".join(formatted_lines)

    def analyze_files(self):
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                file_path = os.path.join(root, file)
                if self.should_ignore(file_path):
                    continue


                relative_path = os.path.relpath(file_path, self.project_path)
                print(f"Analyzing {file_path}")
                self.analyze_file(file_path, relative_path)

    def analyze_tree(self):
        tree_structure = self.read_tree_file()
        print("Tree structure:")
        print(tree_structure)

        print("\nllm: analyze tree now")

        for analyzer_dir in self.analyzers:
            system_prompt, user_prompt = load_prompt(analyzer_dir, 2)
            user_prompt = user_prompt.replace("{tree_structure}", tree_structure)

            response = chat_completion_create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            analysis = response.choices[0].message.content
            analysis = self.format_markdown(analysis)

            analyzer_name = os.path.basename(analyzer_dir)
            analysis_file_path = os.path.join(self.output_dir, f"analysis_{analyzer_name}.md")
            with open(analysis_file_path, "w") as analysis_file:
                analysis_file.write(analysis)
            print(f'   wrote info to {analysis_file_path}')

        print("\nllm: analyze tree - completed")

    def perform_high_level_analysis(self):
        analysis_summaries = {}

        for analyzer_dir in self.analyzers:
            analyzer_name = os.path.basename(analyzer_dir)
            analysis_summaries[analyzer_name] = []

            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    if f"-{analyzer_name}.md" in file:
                        file_path = os.path.join(root, file)
                        filename = file_path[:-len(f"-{analyzer_name}.md")]
                        with open(file_path, 'r', encoding='utf-8') as f:
                            analysis_summaries[analyzer_name].append(f"Filename: {filename}")
                            analysis_summaries[analyzer_name].append(f.read())
                            analysis_summaries[analyzer_name].append("\n\n\n")

        tree_structure = self.read_tree_file()

        for analyzer_name, content_list in analysis_summaries.items():
            combined_content = "\n\n".join(content_list)
            analyzer_path = f"analyzer/{analyzer_name}"
            system_prompt, user_prompt = load_prompt(analyzer_path, 2)
            user_prompt = user_prompt.replace("{content}", combined_content).replace("{tree_structure}", tree_structure)

            response = chat_completion_create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            high_level_analysis = response.choices[0].message.content
            high_level_analysis = self.format_markdown(high_level_analysis)
            high_level_analysis_path = os.path.join(self.output_dir, f"high_level_analysis_{analyzer_name}.md")
            with open(high_level_analysis_path, "w") as file:
                file.write(high_level_analysis)
            print(f'   wrote high level analysis to {high_level_analysis_path}')

    def analyze(self):
        self.setup_output_directory()
        self.load_gitignore()  # Load .gitignore patterns
        self.generate_tree_structure()
        #self.analyze_tree()
        self.analyze_files()
        self.perform_high_level_analysis()  # Perform the high-level analysis


def parse_arguments():
    parser = argparse.ArgumentParser(description="Analyze a project directory.")
    parser.add_argument("project_path", help="Path to the project directory.")
    return parser.parse_args()


def main():
    args = parse_arguments()
    analyzer = ProjectAnalyzer(args.project_path)
    analyzer.analyze()


if __name__ == "__main__":
    main()

