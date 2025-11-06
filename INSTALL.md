# Rozet Installation Guide

## Quick Install (Global Command)

To install `rozett` command globally so you can run it from anywhere:

```bash
cd /path/to/rozet
bash scripts/install_global.sh
```

This will:
1. Install `rozett` to `~/.local/bin/`
2. Add it to your PATH (if needed)
3. Make it executable from any directory

## Manual Installation

If you prefer to install manually:

```bash
# Create bin directory if it doesn't exist
mkdir -p ~/.local/bin

# Create symlink or copy the rozet script
ln -s /path/to/rozet/rozet ~/.local/bin/rozett

# Add to PATH (if not already there)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Verify Installation

```bash
# Test from any directory
cd /tmp
rozett --help

# Should show Rozet orchestrator help
```

## Using ROZET_HOME

If you move the Rozet project directory, you can set `ROZET_HOME`:

```bash
export ROZET_HOME=/path/to/rozet
rozett --repl
```

## Uninstall

```bash
rm ~/.local/bin/rozett
```

## Troubleshooting

**Command not found:**
- Make sure `~/.local/bin` is in your PATH
- Run `source ~/.zshrc` (or `source ~/.bashrc`)
- Check: `echo $PATH | grep local`

**Wrong directory:**
- Set `ROZET_HOME` environment variable
- Or re-run `scripts/install_global.sh`

