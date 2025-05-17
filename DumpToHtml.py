import re
import os

def parse_dump_file(text):
    # Split text into dump sections
    pattern = r'-+\s+(.*?)\s+Dump Start\s+-+'
    sections = re.split(pattern, text)[1:]  # Skip first empty element
    
    # Organize sections in pairs (name, content)
    structured_data = []
    for i in range(0, len(sections), 2):
        if i+1 < len(sections):
            name = sections[i]
            content = sections[i+1]
            
            # Extract basic properties
            name_match = re.search(r'Name:\s+(.*)', content)
            class_match = re.search(r'Class:\s+(.*)', content)
            path_match = re.search(r'Path:\s+(.*)', content)
            
            if name_match and class_match and path_match:
                item = {
                    'name': name_match.group(1).strip(),
                    'class': class_match.group(1).strip(),
                    'path': path_match.group(1).strip(),
                    'properties': {},
                    'children': []
                }
                
                # Extract properties
                props_match = re.search(r'Properties:\s+(.*?)(?=Children:|$)', content, re.DOTALL)
                if props_match:
                    props_text = props_match.group(1)
                    prop_pattern = r'([A-Z0-9_]+)\s+=\s+"([^"]*)"(?:\s+$ (.*?) $ )?'
                    for prop_match in re.finditer(prop_pattern, props_text):
                        prop_name = prop_match.group(1)
                        prop_value = prop_match.group(2)
                        prop_attribute = prop_match.group(3) if prop_match.group(3) else ""
                        item['properties'][prop_name] = {
                            'value': prop_value,
                            'attribute': prop_attribute
                        }
                
                # Extract children
                children_section = re.search(r'Children:\s+Count:\s+(\d+)(.*?)(?=-+|$)', content, re.DOTALL)
                if children_section and children_section.group(2):
                    children_text = children_section.group(2)
                    children = re.findall(r'#\d+:\s+Name\s+=\s+"([^"]+)",\s+Class\s+=\s+"([^"]+)"', children_text)
                    for child_name, child_class in children:
                        item['children'].append({
                            'name': child_name,
                            'class': child_class
                        })
                
                structured_data.append(item)
    
    return structured_data

def generate_html(data):
    # Sort items to make sure Root is first
    data.sort(key=lambda x: 0 if x['name'] == 'Root' else 1)
    
    # Build a dictionary to quickly find items by path
    items_by_path = {item['path']: item for item in data}
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="windows-1252">
    <title>MA Dump</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1e1e1e;
            color: #e0e0e0;
            line-height: 1.6;
        }
        
        h1 {
            color: #8ab4f8;
            text-align: center;
            margin-bottom: 20px;
            font-weight: 300;
        }
        
        .search-container {
            max-width: 1200px;
            margin: 20px auto;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        
        #searchInput {
            padding: 10px 15px;
            width: 50%;
            min-width: 300px;
            border-radius: 25px;
            border: none;
            background-color: #333;
            color: #e0e0e0;
            font-size: 16px;
            outline: none;
        }
        
        .search-info {
            text-align: center;
            margin: 10px 0;
            font-size: 14px;
            color: #888;
        }
        
        .tree-view {
            max-width: 1200px;
            margin: 0 auto;
            background-color: rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .tree-view ul {
            list-style-type: none;
            padding-left: 25px;
        }
        
        .tree-item {
            cursor: pointer;
            user-select: none;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 4px;
            border-left: 3px solid #8ab4f8;
        }
        
        .tree-item:hover {
            background-color: #353535;
        }
        
        .tree-item::before {
            content: "+";
            display: inline-block;
            width: 20px;
            height: 20px;
            line-height: 20px;
            text-align: center;
            margin-right: 10px;
            background-color: #505050;
            color: #e0e0e0;
            border-radius: 3px;
            font-size: 14px;
        }
        
        .tree-item.open::before {
            content: "-";
            background-color: #8ab4f8;
            color: #1e1e1e;
        }
        
        .hidden {
            display: none;
        }
        
        .tree-content {
            padding: 5px 0 5px 20px;
            margin-left: 10px;
            border-left: 1px dashed #444;
        }
        
        .properties-table {
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.9em;
            width: 100%;
            box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            overflow: hidden;
        }
        
        .properties-table th {
            background-color: #252525;
            padding: 10px;
            text-align: left;
            font-weight: 500;
            border: 1px solid #444;
        }
        
        .properties-table td {
            padding: 8px 10px;
            border: 1px solid #444;
        }
        
        .properties-table tr:nth-child(odd) {
            background-color: #282828;
        }
        
        .properties-table tr:nth-child(even) {
            background-color: #2d2d2d;
        }
        
        .properties-table tr:hover {
            background-color: #353535;
        }
        
        .read-only {
            color: #888;
        }
        
        strong {
            color: #8ab4f8;
            font-weight: 500;
        }
        
        /* Search highlight */
        mark {
            background-color: rgba(138, 180, 248, 0.3);
            color: #8ab4f8;
            border-radius: 2px;
            padding: 0 2px;
            font-weight: bold;
        }
        
        .match-count {
            color: #8ab4f8;
            font-weight: 500;
        }
        
        .no-results {
            text-align: center;
            padding: 20px;
            font-style: italic;
            color: #888;
        }
        
        /* Button styles */
        .button {
            margin-left: 10px;
            padding: 10px 15px;
            border-radius: 25px;
            border: none;
            background-color: #505050;
            color: #e0e0e0;
            font-size: 16px;
            cursor: pointer;
        }
        
        .button:hover {
            background-color: #8ab4f8;
            color: #1e1e1e;
        }
        
        /* Spinner */
        .spinner {
            display: none;
            margin-left: 10px;
            border: 3px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top: 3px solid #8ab4f8;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .search-active .node-hidden {
            display: none;
        }
    </style>
</head>
<body>
    <h1>MA Dump</h1>
    <div class="search-container">
        <input type="text" id="searchInput" placeholder="Search for nodes, properties, or values...">
        <button id="searchButton" class="button" onclick="performSearch()">Search</button>
        <button id="clearButton" class="button" onclick="clearSearch()">Clear</button>
        <div id="spinner" class="spinner"></div>
    </div>
    <div class="search-info" id="searchInfo"></div>
    <div class="no-results hidden" id="noResults">No results found. Try a different search term.</div>
    <div class="tree-view">
"""
    
    # Recursive function to generate HTML tree
    def generate_tree_html(item):
        result = ""
        result += f'<div class="tree-item" onclick="toggleNode(this)">{item["name"]} - {item["class"]}</div>\n'
        result += f'<ul class="tree-content hidden">\n'
        
        # Add basic properties
        result += '<li><strong>Path:</strong> ' + item['path'] + '</li>\n'
        
        # Add properties table
        if item['properties']:
            result += '<li><strong>Properties:</strong>\n'
            result += '<table class="properties-table">\n'
            result += '<tr><th>Name</th><th>Value</th></tr>\n'
            
            for prop_name, prop_data in item['properties'].items():
                css_class = ' class="read-only"' if prop_data['attribute'] == "Read Only" else ''
                result += f'<tr{css_class}><td>{prop_name}</td><td>"{prop_data["value"]}"</td></tr>\n'
                
            result += '</table>\n'
            result += '</li>\n'
        
        # Add children
        for child in item['children']:
            child_path = f"{item['path']}/{child['name']}"
            if child_path in items_by_path:
                result += '<li>\n'
                result += generate_tree_html(items_by_path[child_path])
                result += '</li>\n'
            else:
                result += f'<li>{child["name"]} - {child["class"]}</li>\n'
        
        result += '</ul>\n'
        return result
    
    # Start with Root
    for item in data:
        if item['name'] == 'Root':
            html += generate_tree_html(item)
            break
    
    html += """    </div>
    <script>
        function toggleNode(element) {
            const content = element.nextElementSibling;
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                element.classList.add('open');
            } else {
                content.classList.add('hidden');
                element.classList.remove('open');
            }
        }
        
        function performSearch() {
            const searchTerm = document.getElementById('searchInput').value.trim().toLowerCase();
            if (searchTerm === '') {
                clearSearch();
                return;
            }
            
            // Show spinner
            document.getElementById('spinner').style.display = 'inline-block';
            document.getElementById('searchInfo').innerHTML = '';
            document.getElementById('noResults').classList.add('hidden');
            
            setTimeout(() => {
                let matchCount = 0;
                const allElements = document.querySelectorAll('.tree-view *');
                
                // Reset previous search
                document.querySelectorAll('.node-hidden').forEach(el => {
                    el.classList.remove('node-hidden');
                });
                
                document.querySelectorAll('mark').forEach(mark => {
                    const parent = mark.parentNode;
                    const text = mark.textContent;
                    const textNode = document.createTextNode(text);
                    parent.replaceChild(textNode, mark);
                });
                
                // Convert NodeList to Array for easier manipulation
                const elementsArray = Array.from(allElements);
                
                // First pass: highlight matches
                elementsArray.forEach(el => {
                    if (el.childNodes && el.childNodes.length > 0) {
                        for (let i = 0; i < el.childNodes.length; i++) {
                            const node = el.childNodes[i];
                            
                            // Skip anything that's not a text node
                            if (node.nodeType !== 3) continue;
                            
                            const text = node.nodeValue;
                            const lowerText = text.toLowerCase();
                            
                            if (lowerText.includes(searchTerm)) {
                                matchCount++;
                                
                                // Highlight matched text
                                const parts = [];
                                let lastIndex = 0;
                                let startIndex;
                                
                                while ((startIndex = lowerText.indexOf(searchTerm, lastIndex)) !== -1) {
                                    // Add text before match
                                    if (startIndex > lastIndex) {
                                        parts.push(document.createTextNode(text.substring(lastIndex, startIndex)));
                                    }
                                    
                                    // Create highlighted match
                                    const mark = document.createElement('mark');
                                    mark.textContent = text.substr(startIndex, searchTerm.length);
                                    parts.push(mark);
                                    
                                    lastIndex = startIndex + searchTerm.length;
                                }
                                
                                // Add text after last match
                                if (lastIndex < text.length) {
                                    parts.push(document.createTextNode(text.substring(lastIndex)));
                                }
                                
                                // Replace original node with highlighted parts
                                const fragment = document.createDocumentFragment();
                                parts.forEach(part => fragment.appendChild(part));
                                
                                node.parentNode.replaceChild(fragment, node);
                                
                                // Expand all parent nodes
                                let parent = el.closest('.tree-content');
                                while (parent) {
                                    parent.classList.remove('hidden');
                                    const parentItem = parent.previousElementSibling;
                                    if (parentItem && parentItem.classList.contains('tree-item')) {
                                        parentItem.classList.add('open');
                                    }
                                    parent = parent.parentNode.closest('.tree-content');
                                }
                            }
                        }
                    }
                });
                
                // Hide non-matching nodes
                if (matchCount > 0) {
                    // Update search info
                    document.getElementById('searchInfo').innerHTML = 
                        `Found <span class="match-count">${matchCount}</span> matches for "${searchTerm}"`;
                } else {
                    document.getElementById('noResults').classList.remove('hidden');
                }
                
                // Hide spinner
                document.getElementById('spinner').style.display = 'none';
            }, 10);
        }
        
        function clearSearch() {
            document.getElementById('spinner').style.display = 'inline-block';
            
            setTimeout(() => {
                // Clear search field
                document.getElementById('searchInput').value = '';
                
                // Clear search info
                document.getElementById('searchInfo').innerHTML = '';
                document.getElementById('noResults').classList.add('hidden');
                
                // Remove all highlighting
                document.querySelectorAll('mark').forEach(mark => {
                    const parent = mark.parentNode;
                    const text = mark.textContent;
                    const textNode = document.createTextNode(text);
                    parent.replaceChild(textNode, mark);
                });
                
                // Reset visibility
                document.querySelectorAll('.node-hidden').forEach(el => {
                    el.classList.remove('node-hidden');
                });
                
                // Reset all nodes to closed state
                document.querySelectorAll('.tree-content').forEach(content => {
                    content.classList.add('hidden');
                });
                
                document.querySelectorAll('.tree-item').forEach(item => {
                    item.classList.remove('open');
                });
                
                // Hide spinner
                document.getElementById('spinner').style.display = 'none';
            }, 10);
        }
        
        // Handle Enter key in search input
        document.getElementById('searchInput').addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                performSearch();
            }
        });
    </script>
</body>
</html>"""
    
    return html

if __name__ == "__main__":
    input_file = 'MaDumpCleaned.txt'
    output_file = 'DumpWeb.html'
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: The file {input_file} does not exist.")
        exit(1)
    
    # Read the file with default encoding
    try:
        with open(input_file, 'r') as file:
            text = file.read()
    except Exception as e:
        print(f"Error reading the file: {e}")
        exit(1)
    
    # Parse the file
    data = parse_dump_file(text)
    
    if not data:
        print("Warning: No data was extracted from the file.")
    
    # Generate HTML
    html = generate_html(data)
    
    # Save HTML
    try:
        with open(output_file, 'w') as file:
            file.write(html)
        print(f"HTML file created successfully: {output_file}")
    except Exception as e:
        print(f"Error writing the HTML file: {e}")
