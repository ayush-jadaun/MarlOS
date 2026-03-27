Start a MarlOS agent node for development/testing.

$ARGUMENTS can be a node ID (e.g. "node-1") or left empty to use "dev-node".

Steps:
1. Set NODE_ID from $ARGUMENTS, defaulting to "dev-node" if empty
2. Check that dependencies are installed: `python -c "import zmq, stable_baselines3; print('deps ok')"`
3. If deps missing, run: `pip install -r requirements.txt`
4. Start the agent: `NODE_ID=$ARGUMENTS python -m agent.main`
5. Tell the user the dashboard will be at http://localhost:3001
