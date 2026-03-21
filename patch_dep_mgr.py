with open('src/services/project_setup/dependency_manager.py') as f:
    content = f.read()

content = content.replace('''from src.services.git_ops import GitManager''', '')
content = content.replace('''        self.git = GitManager()''', '')
content = content.replace('''        try:
            await self.git._run_git(["add", "."])

            if await self.git.commit_changes(
                "Initialize project with AC-CDD structure and dev dependencies"
            ):
                logger.info("✓ Changes committed.")

                try:
                    remote_url = await self.git.get_remote_url()
                    if remote_url:
                        current_branch = await self.git.get_current_branch()
                        logger.info(f"Pushing {current_branch} to origin...")
                        await self.git.push_branch(current_branch)
                        logger.info("✓ Successfully pushed to remote.")
                    else:
                        logger.info("No remote 'origin' configured. Skipping push.")
                except Exception as e:
                    logger.warning(f"Failed to push to remote: {e}")
            else:
                logger.info("No changes to commit.")

        except Exception as e:
            logger.warning(f"Git operations failed: {e}")''', '''        try:
            await self.runner.run_command(["git", "add", "."], check=True)
            await self.runner.run_command(["git", "commit", "-m", "Initialize project with AC-CDD structure and dev dependencies"], check=False)
            logger.info("✓ Changes committed.")
        except Exception as e:
            logger.warning(f"Git operations failed: {e}")''')

with open('src/services/project_setup/dependency_manager.py', 'w') as f:
    f.write(content)
