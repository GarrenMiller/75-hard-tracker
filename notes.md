## Technologies

- Use Flask for backend API
- SQLite database
- SolidJS as the frontend framework


## Project Rules

- Everything must run in a Docker container
- Multiple containers (one for each service) is ok
- All tests must be run purely in Docker
- Thorough API testing is necessary
- All development dependencies must be managed with the container. Nothing should need to be installed on the host machine.
- Need thorough unit tests


## MVP Plan
We want API to help us track progess against several different goals, and a UI to show the progress towards the goals. All the information should be saved in the database. Here's a laundry-list of big-ticket items we need:

- Users: People need to be able to sign in to the app.
- User Profiles: Users need to be able to see their progress and manage their current goal(s)
- Goals: Goals should be configurable and represent many different concepts. For example, drinking 1 gallon of water a day is a goal. Working out 3 times a week is also a goal. We need to be able to add new types of goals with new conditions.
- Goal Composition: A user will want to track multiple goals symultaneously. This could be called a Plan.
- Plans: Users will want different difficulties of plans. For instance, some will want to restart their plan when any of their goals have lapsed. Others will want a few "redemption" days before hard failure. This needs to be supported.
- Proof of Completion: There should be the option to provide different types of proof that a task was completed. Think using a GPS location for a set amount of time to verify that they were actually at the gym. Or having several other users acknowledge their completion of the task.
