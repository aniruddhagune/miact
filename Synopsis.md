1.	Title of the Project: Multi-source Information Aggregation & Comparison Tool — MIACT

2.	Introduction: One of the primary use cases of Internet access for many users is access to news and opinions on topics relevant to them. The meteoric rise in the availability of the Internet is reflected in the growing number of platforms and sources that share information and news, which is not always reliable, consistent, or objective. As information is distributed across numerous websites, blogs, and media outlets, users are often exposed to conflicting facts, unverified claims, and opinion-driven narratives. 
Verifying information or comparing viewpoints therefore requires consulting multiple sources, increasing both effort and the likelihood of bias.
In this context, automated systems that can aggregate information from multiple sources and analyze it systematically have become increasingly valuable. By organizing unstructured data, distinguishing objective facts from subjective opinions, and identifying agreement or conflict among sources, such applications support more informed decision-making and critical analysis, making them highly relevant in today’s information-driven society.

3.	Problem Statement: With the super-abundance of sources on the internet, users often experience research fatigue when trying to gather and compare opinions and factual details about products, events, or topics from multiple online sources. 
Understanding the strengths and weaknesses of a product requires reading multiple reviews, each with subjective viewpoints and sometimes conflicting claims, making it difficult to isolate factual specifications from opinions. 
Similarly, even news reporting can contain inaccuracies, unverified claims, or opinionated language presented as fact, leading to misunderstandings or misinformation.

4.	Proposed System: The proposed system is a locally executable application with a browser-based interface developed using Streamlit. It is designed to assist users in efficiently analyzing information collected from multiple online sources without requiring user accounts or external cloud services. The system operates through the following components:
•	The application collects data from multiple web sources using web scraping techniques.
•	The collected data is stored locally in a single database, separating structured objective information from unstructured or semi-structured subjective text.
•	Natural Language Processing (NLP) techniques are used to analyze the collected text and classify content into objective facts and subjective opinions.
•	Objective information is normalized and compared across sources to identify confirmed data and highlight inconsistencies or conflicts.
•	Subjective information is analyzed to summarize opinions and sentiments related to specific aspects, such as product features or key topics.
•	The final results are presented through an interactive interface, displaying verified facts, conflicting information, and summarized opinions in a clear and user-friendly manner.
By automating data collection, classification, & comparison, the proposed system reduces research effort, improves information reliability, and enables informed decision-making.
5.	Usability: The system is designed with simplicity and accessibility as key considerations. Users interact with the application through a browser-based interface that requires no account creation, installation, or prior technical knowledge. Input is limited to a minimal number of fields, allowing users to quickly enter a query such as a product name or topic and receive results without navigating complex menus.

Information is presented in a clear and organized manner, with objective facts and subjective opinions displayed separately to reduce confusion. Conflicting information is explicitly highlighted, helping users quickly identify areas that may require further attention.
Since the application runs locally and can be accessed through a web browser, it can be conveniently used as a pinned tab or a quick-reference tool during research.

6.	Objectives: 
•	To design and develop a locally executable application for aggregating information from multiple online sources.
•	To collect and organize unstructured web data into a structured and comparable format.
•	To distinguish objective factual information from subjective opinions using Natural Language Processing techniques.
•	To identify confirmed information and highlight conflicts or inconsistencies across different sources.
•	To summarize & analyze opinions and sentiments related to specific aspects or features.
•	To reduce research fatigue by presenting consolidated facts and summarized opinions through an intuitive interface.
•	To support informed decision-making by improving clarity, reliability, and accessibility of online information.

7.	Functional Requirements:
•	The system shall accept a user query such as a product name or topic through a browser-based interface.
•	The system shall collect relevant information from multiple predefined online sources based on the user input.
•	The system shall extract and organize objective factual information from the collected data.
•	The system shall identify and separate subjective opinions from objective facts.
•	The system shall compare factual information across sources to detect agreements and conflicts.
•	The system shall analyze subjective text to summarize opinions and sentiment related to specific aspects.
•	The system shall store processed data locally for efficient retrieval and comparison.
•	The system shall present consolidated facts, conflicts, and opinion summaries in a clear and structured format.

8.	Non-Functional Requirements:
•	Usability: The system shall provide a simple and intuitive interface that requires minimal user effort and no prior training.
•	Performance: The system shall process and present results within a reasonable time for typical user queries.
•	Portability: The system shall be accessible through any modern web browser across different devices.
•	Scalability: The system shall support adding new sources or topics without significant changes to the core architecture.
•	Reliability: The system shall handle unavailable or inconsistent sources gracefully without system failure.
•	Security: The system shall not require user authentication and shall avoid storing sensitive user data.
•	Maintainability: The system shall be modular and organized to allow easy updates and enhancements.

9.	Hardware & Software Requirements: 
The Hardware requirements are as follows:
•	Any device capable of running a modern web browser, including:
o	Desktop or laptop computer
o	Smartphone or tablet
•	Minimum 4 GB RAM recommended (device-dependent)
•	Stable internet connection (required for data collection and content updates)
•	Local storage availability for temporary caching and settings
	The Software requirements are as follows:
•	Any Operating System that supports a web browser, such as Windows, Linux, Android, iOS or macOS
•	Web Browser: Any modern web browser (Chrome, Firefox, Edge, Safari)

10.	Frontend: React/Vite

11.	Backend: Python is used due to its extensive ecosystem for web scraping, data processing, & Natural Language Processing. Libraries such as BeautifulSoup, Pandas, & NLP toolkits enable efficient extraction, classification, & analysis of unstructured text.
12.	Database: PostgreSQL is used as the backend database to store both structured factual data and semi-structured textual data. Its support for relational tables as well as JSON-based storage makes it suitable for managing heterogeneous data within a single database system.

13.	Architecture Overview: The system is designed using a layered architecture to ensure clear separation of responsibilities and ease of maintenance. Each layer performs a specific role in the overall data processing workflow, and higher layers depend only on the services provided by lower layers.
•	Presentation Layer: Streamlit User Interface
•	Application Layer: Scraping Module, Preprocessing Module, Classification & Comparison Modules
•	Data Layer: PostgreSQL Database
 
14.	Modules Description: 
•	User Input Module (Streamlit) — Accepts user input such as a product name or topic through a simple browser-based interface.
•	Web Scraping Module (Requests, BeautifulSoup) — Retrieves relevant information from multiple online sources based on the user’s query.
•	Data Preprocessing Module (Python, Pandas) — Cleans and organizes the scraped data by removing unnecessary content, normalizing text, and converting it into a consistent structure suitable for analysis.
•	Fact and Opinion Classification Module (spaCy, NLTK) — Analyzes processed text to distinguish objective factual statements from subjective opinions using basic Natural Language Processing techniques.
•	Conflict Identification Module (Pandas, NumPy) — Compares extracted factual information across different sources to identify commonly agreed-upon facts and highlight conflicting or inconsistent data.
•	Opinion and Sentiment Analysis Module (VADER) — Processes subjective text to determine sentiment and summarize opinions related to specific aspects or features.
•	Data Storage Module (PostgreSQL) — Stores structured factual data, subjective opinions, and source metadata to facilitate efficient retrieval and comparison.
•	Presentation Module (Streamlit) — Displays consolidated facts, detected conflicts, and summarized opinions in a clear and user-friendly format through the browser-based interface.

15.	Conclusion: The project aims to provide a simple and practical tool for organizing and comparing information gathered from multiple online sources. By separating objective facts from subjective opinions and highlighting areas of agreement or conflict, the system helps users reduce the effort involved in manual research. Rather than attempting to replace existing news platforms or review websites, the application is intended to function as a lightweight companion tool that can be accessed easily through a browser, such as a pinned tab. Its local execution and minimal user requirements make it convenient for quick checks, comparisons, and exploratory analysis. Through this project, fundamental concepts of data science and Natural Language Processing are applied in a realistic and manageable manner.

