import { render } from "solid-js/web";
import { Router, Route } from "@solidjs/router";
import App from "./App";
import Dashboard from "./pages/Dashboard";
import Plans from "./pages/Plans";
import Goals from "./pages/Goals";
import PlanDetail from "./pages/PlanDetail";
import PlanForm from "./pages/PlanForm";
import Login from "./pages/Login";
import Register from "./pages/Register";
import "@fontsource-variable/space-grotesk";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/ibm-plex-mono/600.css";
import "@fontsource/ibm-plex-mono/700.css";
import "./index.css";

render(
  () => (
    <Router>
      <Route path="/" component={App}>
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <Route path="/" component={Dashboard} />
        <Route path="/plans" component={Plans} />
        <Route path="/plans/:id" component={PlanDetail} />
        <Route path="/plans/:id/edit" component={PlanForm} />
        <Route path="/goals" component={Goals} />
      </Route>
    </Router>
  ),
  document.getElementById("root")!,
);
