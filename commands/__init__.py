import os
from importlib import import_module

async def setup(bot):
    for filename in os.listdir(os.path.dirname(__file__)):
        if filename.endswith('.py') and not filename.startswith('_'):
            cog_name = filename[:-3]
            try:
                module = import_module(f'commands.{cog_name}')
                if hasattr(module, 'setup'):
                    await module.setup(bot)
                    print(f'✅ Loaded cog: {cog_name}')
                else:
                    print(f'⚠️ No setup() found in: {cog_name}')
            except Exception as e:
                print(f'❌ Failed to load {cog_name}: {e}')