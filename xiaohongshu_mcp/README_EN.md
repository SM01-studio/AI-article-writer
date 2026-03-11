# Xiaohongshu (RED) Auto Search & Comment Tool (MCP Server 2.0)

<div align="right">

English | [中文](README.md)

</div>

> This project is based on [JonaFly/RednoteMCP](https://github.com/JonaFly/RednoteMCP.git) with comprehensive optimizations and feature extensions based on multiple practical experiences (by windsurf). Sincere thanks to the original author for their contributions!

This is a Xiaohongshu (RED) automatic search and comment tool developed with Playwright. As an MCP Server, it can be integrated with MCP Clients (such as Claude for Desktop) through specific configurations, helping users automatically log in to Xiaohongshu, search for keywords, retrieve note content, and publish AI-generated comments.

## Key Features and Advantages

- **Deep AI Integration**: Leverages the large model capabilities of MCP clients (like Claude) to generate more natural and relevant comment content
- **Modular Design**: Divides functionality into three independent modules: note analysis, comment generation, and comment publishing, improving code maintainability
- **Powerful Content Retrieval**: Integrates multiple methods to retrieve note content, ensuring complete acquisition of titles, authors, and content from various types of notes
- **Persistent Login**: Uses persistent browser context, eliminating the need to log in repeatedly after the first login
- **Two-Step Comment Process**: First obtains note analysis results, then generates and publishes comments through the MCP client

## Version 2.0 Major Improvements

- **Enhanced Content Retrieval**: Restructured the note content retrieval module, increased page loading wait times and scrolling operations, implementing four different content retrieval methods
- **AI Comment Generation**: Redesigned the comment functionality to return note analysis results to the MCP client, which uses its AI capabilities to generate more natural and relevant comments
- **Modular Functionality**: Divided functionality into three independent modules: note analysis, comment generation, and comment publishing, improving code maintainability
- **Search Results Optimization**: Resolved the issue of titles not displaying when searching for notes, providing more complete search results
- **Enhanced Error Handling**: Added more detailed error handling and debug information output

## I. Core Features

### 1. User Authentication and Login
- **Persistent Login**: Supports manual QR code login, saves state after first login, no need to scan again for subsequent use
- **Login State Management**: Automatically detects login status and prompts users to log in when needed

### 2. Content Discovery and Retrieval
- **Smart Keyword Search**: Supports multi-keyword search, can specify the number of results to return, and provides complete note information
- **Multi-dimensional Content Retrieval**: Integrates four different retrieval methods to ensure accurate acquisition of note titles, authors, publication times, and content
- **Comment Data Retrieval**: Supports retrieving comments on notes, including commenter, comment text, and time information

### 3. Content Analysis and Generation
- **Note Content Analysis**: Automatically analyzes note content, extracts key information, and identifies the domain of the note
- **AI Comment Generation**: Uses the AI capabilities of MCP clients (such as Claude) to generate natural, relevant comments based on note content
- **Multiple Comment Types**: Supports four different types of comment generation:
  - **Traffic-driving**: Guides users to follow or private message
  - **Like-oriented**: Simple interactions to gain goodwill
  - **Inquiry-based**: Increases interaction in the form of questions
  - **Professional**: Displays professional knowledge to establish authority

### 4. Data Return and Feedback
- **Structured Data Return**: Returns note analysis results to the MCP client in JSON format, facilitating AI comment generation
- **Comment Publishing Feedback**: Provides real-time feedback on comment publishing results

## II. Installation Steps

1. **Python Environment Preparation**: Ensure your system has Python 3.8 or higher installed. If not, download and install it from the official Python website.

2. **Project Acquisition**: Clone or download this project to your local machine.

3. **Create Virtual Environment**: Create and activate a virtual environment in the project directory (recommended):
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install Dependencies**: Install the required dependencies in the activated virtual environment:
   ```bash
   pip install -r requirements.txt
   pip install fastmcp
   ```

5. **Install Browser**: Install the browsers required by Playwright:
   ```bash
   playwright install
   ```

## III. MCP Server Configuration

Add the following content to the MCP Client (such as Claude for Desktop) configuration file to configure this tool as an MCP Server:

### Mac Configuration Example

```json
{
    "mcpServers": {
        "xiaohongshu MCP": {
            "command": "/absolute/path/to/venv/bin/python3",
            "args": [
                "/absolute/path/to/xiaohongshu_mcp.py",
                "--stdio"
            ]
        }
    }
}
```

### Windows Configuration Example

```json
{
    "mcpServers": {
        "xiaohongshu MCP": {
            "command": "C:\\Users\\username\\Desktop\\MCP\\Redbook-Search-Comment-MCP2.0\\venv\\Scripts\\python.exe",
            "args": [
                "C:\\Users\\username\\Desktop\\MCP\\Redbook-Search-Comment-MCP2.0\\xiaohongshu_mcp.py",
                "--stdio"
            ]
        }
    }
}
```

> **Important Notes**:
> - Please use the **complete absolute path** of the Python interpreter in your virtual environment
> - Mac example: `/Users/username/Desktop/RedBook-Search-Comment-MCP/venv/bin/python3`
> - Windows example: `C:\Users\username\Desktop\MCP\Redbook-Search-Comment-MCP2.0\venv\Scripts\python.exe`
> - Similarly, xiaohongshu_mcp.py also needs to use a **complete absolute path**
> - Backslashes in Windows paths need to be double-escaped in JSON (using `\\`)

### Python Command Differences (python vs python3)

In different system environments, Python commands may vary depending on your system configuration. Here's how to determine which command you should use:

1. **Determine Your Python Command**:
   - Run in terminal: `python --version` and `python3 --version`
   - Check which command returns a Python 3.x version (this project requires Python 3.8+)

2. **Confirm in Virtual Environment**:
   - After activating the virtual environment, run `which python` or `where python` (Windows)
   - This will display the complete path of the Python interpreter

3. **Use the Correct Command in Configuration**:
   - Mac: Usually `python3` or `python` in the virtual environment
   - Windows: Usually `python` or `python.exe`

In the configuration file, always use the **complete absolute path** of the Python interpreter in your virtual environment, not the command name.

## IV. Usage Methods

### (A) Starting the Server

1. **Direct Execution**: In the project directory, after activating the virtual environment, execute:
   ```bash
   python3 xiaohongshu_mcp.py
   ```

2. **Launch via MCP Client**: After configuring the MCP Client, follow the client's operation process to start and connect.

### (B) Main Functionality Operations

After connecting to the server in the MCP Client (such as Claude for Desktop), you can use the following features:

### 1. Log in to Xiaohongshu

**Tool Function**:
```
mcp0_login()
```

**Usage in MCP Client**:
Send the following text directly:
```
Help me log in to my Xiaohongshu account
```
Or:
```
Please log in to Xiaohongshu
```

**Function Description**: When used for the first time, it will open a browser window and wait for the user to manually scan the QR code to log in. After successful login, the tool will save the login state.

### 2. Search for Notes

**Tool Function**:
```
mcp0_search_notes(keywords="keywords", limit=5)
```

**Usage in MCP Client**:
Send a search request containing keywords:
```
Help me search for Xiaohongshu notes with the keyword: food
```
Specify the number of results:
```
Help me search for Xiaohongshu notes with the keyword travel, return 10 results
```

**Function Description**: Searches for Xiaohongshu notes based on keywords and returns a specified number of results. Returns 5 results by default.

### 3. Get Note Content

**Tool Function**:
```
mcp0_get_note_content(url="note URL")
```

**Usage in MCP Client**:
Send a request containing the note URL:
```
Help me get the content of this note: https://www.xiaohongshu.com/search_result/xxxx
```
Or:
```
Please check the content of this Xiaohongshu note: https://www.xiaohongshu.com/search_result/xxxx
```

**Function Description**: Retrieves detailed content of the specified note URL, including title, author, publication time, and content.

### 4. Get Note Comments

**Tool Function**:
```
mcp0_get_note_comments(url="note URL")
```

**Usage in MCP Client**:
Send a comment request containing the note URL:
```
Help me get the comments on this note: https://www.xiaohongshu.com/search_result/xxxx
```
Or:
```
Please check the comment section of this Xiaohongshu note: https://www.xiaohongshu.com/search_result/xxxx
```

**Function Description**: Retrieves comment information for the specified note URL, including commenter, comment content, and comment time.

### 5. Post Smart Comment

**Tool Function**:
```
mcp0_post_smart_comment(url="note URL", comment_type="comment type")
```

**Usage in MCP Client**:
Send a request containing the note URL and comment type:
```
Help me write a [type] comment for this note: https://www.xiaohongshu.com/explore/xxxx
```

**Function Description**: Retrieves note analysis results and returns them to the MCP client, which generates a comment and calls post_comment to publish it.

### 6. Post Comment

**Tool Function**:
```
mcp0_post_comment(url="note URL", comment="comment content")
```

**Usage in MCP Client**:
Send a request containing the note URL and comment content:
```
Help me post this comment to the note: https://www.xiaohongshu.com/explore/xxxx
Comment content: [comment content]
```

**Function Description**: Posts the specified comment content to the note page.

## V. User Guide

### 0. Working Principle

This tool uses a two-step process to implement smart commenting:

1. **Note Analysis**: Calls the `post_smart_comment` tool to get note information (title, author, content, etc.)

2. **Comment Generation and Publishing**:
   - The MCP client (such as Claude) generates comments based on note analysis results
   - Calls the `post_comment` tool to publish the comment

This design fully utilizes the AI capabilities of the MCP client to generate more natural and relevant comments.

### 1. Usage in MCP Client

#### Basic Operations

| Function | Example Command |
|---------|----------|
| **Search Notes** | `Help me search for Xiaohongshu notes about [keyword]` |
| **Get Note Content** | `Help me view the content of this Xiaohongshu note: https://www.xiaohongshu.com/explore/xxxx` |
| **Analyze Note** | `Help me analyze this Xiaohongshu note: https://www.xiaohongshu.com/explore/xxxx` |
| **Get Comments** | `Help me view the comments on this note: https://www.xiaohongshu.com/explore/xxxx` |
| **Generate Comment** | `Help me write a [type] comment for this Xiaohongshu note: https://www.xiaohongshu.com/explore/xxxx` |

#### Comment Type Options

| Type | Description | Use Case |
|---------|------|----------|
| **Traffic-driving** | Guide users to follow or private message | Increase followers or private message interactions |
| **Like-oriented** | Simple interactions to gain goodwill | Increase exposure and interaction rate |
| **Inquiry-based** | Increase interaction in the form of questions | Trigger blogger replies, increase interaction depth |
| **Professional** | Display professional knowledge to establish authority | Build professional image, enhance credibility |

### 2. Actual Workflow Example

```
User: Help me write a professional type comment for this Xiaohongshu note: https://www.xiaohongshu.com/explore/xxxx

Claude: I'll help you write a professional type comment. Let me get the note content and generate a comment.
[Calls post_smart_comment tool]

# Tool returns note analysis results, including title, author, content, domain, and keywords

Claude: I've obtained the note information, this is a note about [topic]. Based on the content, I generated and posted the following professional comment:

"[Generated professional comment content]"

[Calls post_comment tool]

Claude: Comment successfully posted!
```

**Note**: In the above process, the `post_smart_comment` tool is only responsible for retrieving note analysis results and returning them to the MCP client. The actual comment generation is done by the MCP client (such as Claude) itself.

### 3. Working Principle

The new version of the Xiaohongshu MCP tool adopts a modular design, divided into three core modules:

1. **Note Analysis Module** (analyze_note)
   - Retrieves the title, author, publication time, and content of the note
   - Analyzes the domain and keywords of the note
   - Returns structured note information

2. **Comment Generation Module** (implemented by the MCP client)
   - Receives note analysis results
   - Generates natural, relevant comments based on note content and comment type
   - Allows users to preview and modify comments before publishing

3. **Comment Publishing Module** (post_comment)
   - Receives generated comment content
   - Locates and operates the comment input box
   - Publishes the comment and returns results

## VI. Code Structure

- **xiaohongshu_mcp.py**: The core file implementing the main functions, including login, search, content and comment retrieval, comment publishing, and other code logic.
- **requirements.txt**: Records the dependencies required by the project.

## VII. Common Issues and Solutions

1. **Connection Failure**:
   - Ensure you're using the **complete absolute path** of the Python interpreter in your virtual environment
   - Ensure the MCP server is running
   - Try restarting the MCP server and client

2. **Browser Session Issues**:
   If you encounter a `Page.goto: Target page, context or browser has been closed` error:
   - Restart the MCP server
   - Reconnect and log in again

3. **Dependency Installation Issues**:
   If you encounter a `ModuleNotFoundError` error:
   - Ensure all dependencies are installed in the virtual environment
   - Check if the fastmcp package is installed

## VIII. Notes and Troubleshooting

### 1. Usage Notes

- **Browser Mode**: The tool runs in Playwright's non-headless mode, opening a real browser window during execution
- **Login Method**: First-time login requires manual QR code scanning; subsequent uses don't require rescanning if the login state is valid
- **Platform Rules**: Please strictly follow Xiaohongshu platform regulations during use, avoid excessive operations to prevent account banning risks
- **Comment Frequency**: It's recommended to control comment posting frequency, avoid posting a large number of comments in a short time, and limit the number of comments posted per day to no more than 30

### 2. Common Issues and Solutions

#### Browser Instance Issues

If you encounter errors like "Page.goto: Target page, context or browser has been closed", it may be due to browser instances not closing correctly or data directory lock file issues. Try:

```bash
# Delete browser lock files
rm -f /project_path/browser_data/SingletonLock /project_path/browser_data/SingletonCookie

# If the problem persists, backup and rebuild the browser data directory
mkdir -p /project_path/backup_browser_data
mv /project_path/browser_data/* /project_path/backup_browser_data/
mkdir -p /project_path/browser_data
```

#### Content Retrieval Issues

If you cannot retrieve note content or the content is incomplete, try:

1. **Increase Wait Time**: Xiaohongshu note pages may need longer loading times, especially for notes with many images or videos
2. **Clear Browser Cache**: Sometimes browser cache can affect content retrieval
3. **Try Different Retrieval Methods**: The tool integrates multiple retrieval methods; if one method fails, try others

#### Platform Changes Adaptation

The Xiaohongshu platform may update page structure and DOM elements, causing the tool to malfunction. If you encounter such issues:

1. **Check Project Updates**: Pay attention to the latest version of the project and update in a timely manner
2. **Adjust Selectors**: If you're familiar with the code, try adjusting CSS selectors or XPath expressions
3. **Submit Issue Feedback**: Submit issues to the project maintainer, describing the specific problems and page changes encountered

## IX. Disclaimer

This tool is for learning and research purposes only. Users should strictly comply with relevant laws, regulations, and Xiaohongshu platform rules. The project developers are not responsible for any issues caused by improper use.
