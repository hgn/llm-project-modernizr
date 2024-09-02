# LLM Project Modernizr

## Overview

**LLM Project Modernizr** is a Python-based project that analyzes software
projects using OpenAI's language models. The tool generates detailed analyses
of the source code, including insights into code quality, API usage, security
concerns, and the overall purpose of the project. The analysis is based on
dynamic prompts and supports multiple OpenAI models, including `gpt-4`,
`gpt-4-turbo`, and `gpt-3.5-turbo`.

## Features

- **Modular Analyzers:** Analyzers are organized into dedicated directories
  under the `analyzer/` folder, allowing for easy customization and extension.
- **Dynamic Model Selection:** Choose from different OpenAI models to tailor
  the analysis to your needs.
- **Detailed Logging:** All requests to the OpenAI API are logged for later
  review.
- **Tree Structure Analysis:** The tool provides a detailed tree structure of
  the project directory and includes it in the analysis.

## Requirements

- Python 3.x
- Virtualenv (optional but recommended)
- An OpenAI API key

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/llm-project-modernizr.git
    cd llm-project-modernizr
    ```

2. **Set up a virtual environment:**

    ```bash
    make venv
    ```

3. **Install the required dependencies:**

    ```bash
    make install
    ```

## Usage

### Running the Analysis

To run the analysis on a software project directory, use the following command:

```bash
venv/bin/python main.py /path/to/your/project
```

The default OpenAI model used is `gpt-3.5-turbo`. If you want to specify a
different model, such as `gpt-4`, you can modify the `Makefile` or run the
script directly:

```bash
venv/bin/python main.py /path/to/your/project --model gpt-4
```

### Cleaning Up

To remove the virtual environment:

```bash
make distclean
```

To remove the generated analysis results:

```bash
make clean
```

## File Structure

- **`main.py`**: The main script that orchestrates the analysis.
- **`Makefile`**: Automates the setup and execution process.
- **`requirements.txt`**: Lists the Python dependencies.
- **`assets/source-code-suffixes.toml`**: Defines file suffixes associated with various programming languages.
- **`analyzer/`**: Contains the modular analyzers, each with its own prompts for analysis.

## Customization

### Adding New Analyzers

1. Create a new directory under `analyzer/`, e.g., `analyzer/new-analyzer/`.
2. Add `stage1.toml` and `stage2.toml` files to the new directory. These files
   should contain the system and user prompts for the initial and high-level
   analyses, respectively.

### Changing the OpenAI Model

You can specify the model to use by passing the `--model` argument when running
the script. The following models are supported:

- `gpt-4`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

## Contributing

Contributions are welcome! If you have any ideas, issues, or suggestions, feel
free to open an issue or a pull request on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
