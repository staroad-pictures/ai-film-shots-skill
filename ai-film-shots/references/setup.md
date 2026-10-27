# Setting up from zero

Allow an afternoon; most of it is sign-ups.

## 1. The computer
- A Mac (Apple silicon) or a PC with at least 100 GB free on the disk that holds the project.
- Recommended on a Mac: Homebrew (brew.sh), then `brew install ffmpeg` in Terminal, for renders longer than Claude's 3-minute commands.

## 2. Claude
- A Claude Max plan at claude.ai (Pro works, but video work uses up its limits within an hour or two).
- The Claude desktop app (claude.ai/download), signed in with the same account.
- In the desktop app, use **Add folder** to give Claude the project folder. Keep the app open and the computer awake while Claude works.

## 3. Higgsfield
- An account at higgsfield.ai with a paid plan. Every generation costs credits.
- In Claude: **Customize > Connectors**, **+ Add**, **Add custom connector**. Name `Higgsfield`, URL `https://mcp.higgsfield.ai/mcp`, Continue, then sign in to Higgsfield.
- Check: in a new chat, ask "What is my Higgsfield credit balance?"

## 4. Magnific
- An account at magnific.com with a paid plan.
- Same steps: custom connector, name `Magnific`, URL `https://mcp.magnific.com`, then sign in (magnific.com/mcp also has an "Add to Claude" button).
- Check: ask "What is my Magnific credit balance?"

## 5. Optional
- ElevenLabs for voice work, Google Drive to exchange files.

## 6. This skill
- Download `ai-film-shots.zip` from the repository's releases (or zip the `ai-film-shots` folder), then add it in Claude's skills settings.
- First message: "Use the ai-film-shots skill. Help me write the continuity file for my film, then tell me my Higgsfield and Magnific balances."
