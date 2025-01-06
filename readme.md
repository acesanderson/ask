# Your friendly IT helper

Ask is a simple command line script that makes a gpt call.

```bash
ask how do
```

It's aware of your system settings and can answer questions about those.

```bash
ask what is my GPU
```

It's preferred to wrap your request (and anything you paste) in double quotes.

```bash
ask "where are my samba config settings"
```

Current default model is `deepseek-chat`, though `claude` and `gpt4` all do a fantastic job.

Conversation history is preserved using Chain's MessageStore class; users can get the history (-hi), last message (-hi), etc.
