# Reward Yourself

**Software Name:** Reward Yourself

**Slogan:** When you're tired from working hard, don't forget to reward yourself properly.

## Introduction

Do you often feel that after working or studying hard, you forget to give yourself the rewards you deserve? *Reward Yourself*  is an app designed for hardworking individuals, encouraging users to appropriately reward themselves after achieving set goals, so as to maintain motivation and happiness.

## Core Functions

- **Effort Table:** Users can list their tasks or goals, such as completing a project, finishing a book, or sticking to a fitness routine for a month. Each time a task is completed, users can record it in this table and earn corresponding points. These points represent your efforts and achievements.
- **Reward Table:** Once enough points are accumulated, users can choose to redeem pre-set rewards in this table. All rewards are defined by the users themselves, which can be a short trip, a delicious meal, a leisurely afternoon tea, etc. The platform does not directly provide material rewards but encourages users to fulfill these little joys by themselves.
- **Point System:** Earning points is not easy and requires users to truly put in effort and time to complete tasks. This setting ensures the value of rewards, preventing them from becoming too easily obtainable and losing their motivational significance.
- **Personalized Settings:** Users can set the difficulty of rewards according to their own situations. For example, if the reward is allowing themselves 20 minutes of gaming time, they should usually stick to staying off the internet to ensure that this reward is attractive enough to themselves.

## Operation

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables:
   Linux:

   ```bash
   export DATA = 'sqlite:///data.db'
   export KEY = 'your_secret_key'
   ```

   Windows PowerShell:

   ```powershell
   $env:DATA = 'sqlite:///data.db'
   $env:KEY = 'your_secret_key'
   ```
3. Initialize the database:

   ```bash
   python init.py
   ```
4. Run the app:

   ```bash
   # For local development environment only
   python app.py
   ```
5. Access the app: Enter `localhost:80` in your browser.

Through this app, we hope users can realize that while working or studying hard, they should not ignore caring for and rewarding themselves. Remember, appropriate rest and rewards can make you go further. Download "Reward Yourself" now and start your rewarding journey!
