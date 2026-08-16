import { render } from "solid-js/web";
import { Router, Route } from "@solidjs/router";
import App from "./App";
import Dashboard from "./pages/Dashboard";
import PlanDetail from "./pages/PlanDetail";
import PlanForm from "./pages/PlanForm";
import GoalForm from "./pages/GoalForm";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import "./index.css";

render(
  () => (
    <Router>
      <Route path="/" component={App}>
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <Route path="/" component={Dashboard} />
        <Route path="/plans/new" component={PlanForm} />
        <Route path="/plans/:id" component={PlanDetail} />
        <Route path="/plans/:id/edit" component={PlanForm} />
        <Route path="/goals/new" component={GoalForm} />
        <Route path="/profile" component={Profile} />
      </Route>
    </Router>
  ),
  document.getElementById("root")!,
);
