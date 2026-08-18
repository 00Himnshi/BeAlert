import { useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";

const projectUrl = import.meta.env.VITE_SUPABASE_URL;
const publicKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

function App() {
  const supabase = useMemo(() => {
    if (!projectUrl || !publicKey) return null;
    return createClient(projectUrl, publicKey);
  }, []);

  const [session, setSession] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [assignments, setAssignments] = useState([]);

  useEffect(() => {
    if (!supabase) return;

    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });
    return () => listener.subscription.unsubscribe();
  }, [supabase]);

  useEffect(() => {
    if (session) loadAssignments();
  }, [session]);

  async function loadAssignments() {
    const { data, error } = await supabase
      .from("assignments")
      .select("title, assignment_url, first_seen_at, last_seen_at")
      .order("first_seen_at", { ascending: false });

    if (error) setMessage(`Could not load assignments: ${error.message}`);
    else setAssignments(data);
  }

  async function signIn(event) {
    event.preventDefault();
    setMessage("Signing in...");
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setMessage(error ? error.message : "Signed in successfully.");
  }

  async function signUp() {
    setMessage("Creating account...");
    const { error } = await supabase.auth.signUp({ email, password });
    setMessage(error ? error.message : "Check your email to confirm your account, then sign in.");
  }

  async function signOut() {
    await supabase.auth.signOut();
    setAssignments([]);
  }

  if (!supabase) {
    return <main className="card"><h1>Assignment Alerts</h1><p>Website configuration is missing. Add the two GitHub Variables described in the README, then publish again.</p></main>;
  }

  if (!session) {
    return (
      <main className="card">
        <h1>Assignment Alerts</h1>
        <p>Sign in to see assignments saved by your automatic checker.</p>
        <form onSubmit={signIn}>
          <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength="6" /></label>
          <button type="submit">Sign in</button>
          <button type="button" className="secondary" onClick={signUp}>Create account</button>
        </form>
        <p className="message">{message}</p>
      </main>
    );
  }

  return (
    <main className="page">
      <header>
        <div><h1>Assignment Alerts</h1><p>Here are the latest assignments along with their links on the ELMS portal.</p></div>
        <button className="secondary" onClick={signOut}>Sign out</button>
      </header>
      <section className="toolbar"><button onClick={loadAssignments}>Refresh list</button><span>{assignments.length} assignment(s) saved</span></section>
      {message && <p className="message">{message}</p>}
      <section className="assignment-list">
        {assignments.length === 0 ? <p>No assignments saved yet. Run the GitHub checker once.</p> : assignments.map((assignment) => (
          <article key={assignment.assignment_url}>
            <h2>{assignment.title}</h2>
            <a href={assignment.assignment_url} target="_blank" rel="noreferrer">Open assignment</a>
            <p>Date: {new Date(assignment.first_seen_at).toLocaleString()}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

export default App;
