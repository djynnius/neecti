# co.nnecti.ng

co.nnecti.ng is a minimalist AI-powered social media platform with unique conversation branching features.

## 🚀 Application Status

The application has been successfully built with the following components:

### ✅ Completed Features

1. **Project Structure** - Flask backend with React frontend
2. **Database Models** - Complete SQLAlchemy models for all entities
3. **Authentication System** - User registration, login, password management
4. **Core API Routes** - Posts, users, following, likes, shares
5. **Real-time Features** - Flask-SocketIO for live updates
6. **AI Translation Service** - Gemma3 integration with MongoDB caching
7. **Private Messaging** - Ephemeral messaging with save option
8. **Notification System** - Real-time notifications with auto-cleanup
9. **Search & Discovery** - Advanced search for users, posts, hashtags
10. **Moderation System** - Content reporting and admin tools
11. **Frontend Application** - React app with Tailwind CSS

### 🏗️ Architecture

**Backend (Flask)**
- **Models**: User, Post, Message, Conversation, Notification, Report
- **Controllers**: Separate controllers for each feature area
- **Routes**: Blueprint-based routing structure
- **Real-time**: SocketIO for live features
- **Translation**: Ollama/Gemma3 integration with MongoDB caching

**Frontend (React)**
- **Context Providers**: Auth, Socket, Theme management
- **Components**: Reusable UI components with Tailwind CSS
- **Pages**: Home, Login, Register, Profile, Messages, etc.
- **Real-time**: Socket.io-client integration

### 🎨 Design System

The app uses a cohesive color scheme:
- Primary Blue: `#093FB4`
- Secondary Blue: `#00CAFF`
- Primary Green: `#06923E`
- Light Gray: `#EAEFEF`
- White: `#FFFFFF`
- Black: `#000000`
- Green: `#06923E`

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL
- MongoDB
- Ollama with Gemma3 model

### Backend Setup

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Initialize database**:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. **Run the application**:
```bash
python app.py
```

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start development server**:
```bash
npm start
```

### External Services Setup

1. **PostgreSQL**: Ensure PostgreSQL is running on `10.102.109.141:5432`
2. **MongoDB**: Ensure MongoDB is running on `10.102.109.249:27017`
3. **Ollama**: Ensure Ollama with Gemma3 is running on `10.102.109.66:11434`

## 📱 Key Features

The general idea is to have a minimalist AI powered social media site. The site will allow people to share thoughts like the original twitter site with limited characters (250 characters max). The site will be mainly a text site with only image sharing supported (maximim of 3 per accompanying text post). 

The app will behave like git in that it will allow for conversation branching. A person may start a conversation and when the conversation gets responses it becomes a tree. At any point a person on the conversation my click on the branch icon and start his/her own tree from the main tree. Anyone following the conversation will be able to follow backt to the top through the branch that leasd to the tree. 

A person can branch of a trending tree which is one that is getting alot of interaction through likes, comments and shares. People can only share to their timeline not to other people. This app will have a private messaging system that deletes after logout exept you click on "save message". 

The apps AI feature will be supporting multiple languages: English, French, Portuguese, German, and Spanish for starters. This language list will be expanded later on. People who speak these languages when they sign up will be able to read conversations in their languages. Gemma 3 will be used to translate conversation to these languages while maintinaing context. People will be able to click on a message to see it in the original language. While original conversations are stored in the database, the translated conversation that retain context should be made on the fly and stored in a cache for quick access. This cache will be in a MongoDB database. The MongoDB will be used only to store translated conversation and nothing else not even likes or replies or shares.

The app will be built on python Falsk. SQLAlchemy will be used for managing database which will be on PostgreSQL. Flask Socket IO will be used for real time updates to chats and conversations. The front wnd will be built with React and Tailwind CSS. 

Theres a way I like my faskapps built. With the following structure:

```
co.nnecti.ng/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   ├── routes/
│   ├── assets (instead of static
│   └── views (instead of templates)
|   |__ controllers (where all the functions and classes required for routes are defined)
|      
├── database/
├── migrations/
├── tests/
├── requirements.txt
├── .env
├── .gitignore
└── app.py
```

Also I like my Flask apps to be built with Blueprints in the routes directory. Each blueprint will have its own directory with an `__init__.py` file to register the blueprint. The models will be in the models directory and will be imported into the routes as needed.

The theme for the app will be light blue and dark blue with a white background and black text [#093FB4, #00CAFF, #EAEFEF, #FFFFFF, #000000]. 

Credentials for Postgre (host=10.102.109.141, user=oracle   password=urimandthumim database=connecting,   port=5432)

mongodb credentials (host=10.102.109.249, user=oracle, password=urimandthumim, database=connecting, port=27017)

the LLM Gemma3 is being served through ollama running on 10.102.109.66:11434




Signup and login 
-----------------
In production signup and login will be done with OAuth2.0 and will support Google, Facebook, and Twitter (X). Phonenumber will be collected at sign up and login willl be with email and password or phone number and password. Passwords will be hashed with bcrypt. MFA will be supported by sending a code to the phone number or email address.

While in development, before production, authentication will be done with a simple username and password. The password will be hashed with bcrypt. and will all be managed by the co.nnecti.ng app.

All users will have handles that have to be unique. Along with their first name and last name. Emails, Phonenumber and handles will be unique. The handle will be used to identify the user in the app. The handle will be used in the URL to access the user's profile page. The URL structure for accessing the user profile/page will be /@handle. The handle will be used to mention users in conversations and comments. The handle will be used to follow users and see their posts on the timeline.

The app will have a timeline that shows the posts of the users that the logged in user is following. The timeline will be updated in real time with Flask Socket IO. The timeline will show the posts in reverse chronological order. The timeline will also show the trending conversations and posts. The trending conversations and posts will be updated in real time with Flask Socket IO.

The app will have a search feature that allows users to search for conversations, posts, and users. The search will be done with a simple keyword search and will return results in real time. The search will also support hashtags and mentions.

The app will have a profile page for each user that shows their posts, followers, following, and bio. The profile page will also show the user's handle, first name, last name, and profile picture. The profile picture will be uploaded by the user and will be stored in the database.

The app will have a settings page where users can change their password, email, phone number, and handle. The settings page will also allow users to delete their account.

The app will have a notifications system that will notify users of new followers, likes, comments, and shares. The notifications will be updated in real time with Flask Socket IO. The notifications will be stored in the database and will be deleted after 10 days.

The app will have a private messaging system that allows users to send messages to each other. The messages will be stored in the database and will be deleted after logout unless the user clicks on "save message". The private messaging system will be updated in real time with Flask Socket IO.

The app will have a reporting system that allows users to report posts, comments, and users. The reports will be stored in the database and will be reviewed by the administrators of the app. The app will have a moderation system that allows administrators to delete posts, comments, and users.

The app will have a dark mode and light mode that can be toggled by the user. The dark mode will use a dark blue background with white text. The light mode will use a white background with black text. The theme colors will be used throughout the app.

The app will have a responsive design that works on both desktop and mobile devices. The app will be built with React and Tailwind CSS to ensure a modern and user-friendly interface.

