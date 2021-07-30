#!/usr/bin/env python3

import argparse
import git
import sys


class TaskException(Exception):
    pass


class TaskCheckException(TaskException):
    def __init__(self, message):
        super().__init__("CHECK FAILED: %s" % message)


class Task():
    branch_names = []

    def __init__(self):
        self.repo = git.Repo('.')

    def reset_branches(self):
        """Delete all branches for this task and checkout them again from origin."""
        self.repo.git.reset('--mixed')
        self.repo.git.checkout('main')
        for branch_name in self.branch_names:
            try:
                self.repo.delete_head(branch_name, force=True)
            except git.exc.GitCommandError:
                pass
            self.repo.git.checkout('origin/' + branch_name, b=branch_name)
        self.repo.git.checkout('main')

    def iter_commits(self, branch_name):
        """Iterate over commits that are in given branch (on top of the tasks branch)."""
        main_head_heaxsha = next(self.repo.iter_commits('origin/tasks')).hexsha
        for commit in self.repo.iter_commits(branch_name):
            if commit.hexsha == main_head_heaxsha:
                break
            yield commit

    def check_old_commits_unchanged(self, old_branch, new_branch):
        """Check all the commits in old branch are unchanged in the new branch
        (have the same hexsha)."""
        new_hexshas = [commit.hexsha for commit in self.iter_commits(new_branch)]
        new_summaries = [commit.summary for commit in self.iter_commits(new_branch)]

        for commit in self.iter_commits(old_branch):
            if commit.hexsha not in new_hexshas:
                if commit.summary not in new_summaries:
                    raise TaskCheckException('A commit is missing: %s' % commit.summary)
                else:
                    raise TaskCheckException(
                        'A commit was unexpectedly modified: %s' % commit.summary
                    )

    def check_commits_count(self, branch, expected_commits_count):
        commits_count = len([commit for commit in self.iter_commits(branch)])
        diff = abs(commits_count - expected_commits_count)
        msg = (
            'Unexpected number of commits in branch {branch} ({diff} {quantifier} than expected).'
        )
        if commits_count > expected_commits_count:
            raise TaskCheckException(msg.format(branch=branch, diff=diff, quantifier='more'))
        if commits_count < expected_commits_count:
            raise TaskCheckException(msg.format(branch=branch, diff=diff, quantifier='less'))


class CherryPick(Task):
    branch_names = ['cherry-pick-main', 'cherry-pick-feature']

    def start(self):
        self.reset_branches()

        print("""
=================
Task: cherry-pick
=================

Cherry-pick into the `cherry-pick-main` branch all the commits that modified \
`source/cheatsheet.md` file in the `cherry-pick-feature` branch that are not yet in the \
`cherry-pick-main` branch.

If the history looks like this:

                      A---B---C---D---E---F feature
                     /
            G---H---I---J main

Then the result should look like this:

                      A---B---C---D---E---F feature
                     /
            G---H---I---J---C`--D` main

(To show only task-related branches in gitk: gitk --branches=cherry-pick-*)
""")


    def check(self):
        # Check all commits from the origin/cherry-pick-main and origin/cherry-pick-feature
        # branches are present.
        self.check_old_commits_unchanged('origin/cherry-pick-main', 'cherry-pick-main')
        self.check_old_commits_unchanged('origin/cherry-pick-feature', 'cherry-pick-feature')

        # Check the commits count
        self.check_commits_count('cherry-pick-feature', 9)
        self.check_commits_count('cherry-pick-main', 6)

        # Check the commit order
        expected_summaries = [
            'Escape the diagram in cheatsheet',
            'Add picture of the basic git workflow',
            'Add commands for working with remote rpositories',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('cherry-pick-main')]
        if main_summaries != expected_summaries:
            raise TaskCheckException(
                'Unexpected commits in cherry-pick-main branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        print("OK")


class ConflictCherryPick(Task):
    branch_names = ['conflict-cherry-pick-main', 'conflict-cherry-pick-feature']

    def start(self):
        self.reset_branches()

        print("""
==========================
Task: conflict-cherry-pick
==========================

Cherry-pick into the `conflict-cherry-pick-main` branch all the commits that modified \
`source/cheatsheet.md` file in the `conflict-cherry-pick-feature` branch that are not yet in the \
`conflict-cherry-pick-main` branch.

If the history looks like this:

                  A---B---C---D---E---F feature
                 /
            G---H---I---J main

Then the result should look like this:

                  A---B---C---D---E---F feature
                 /
            G---H---I---J---C`--D` main

(To show only task-related branches in gitk: gitk --branches=conflict-cherry-pick-*)
""")


    def check(self):
        # Check all commits from the origin/conflict-cherry-pick-main and
        # origin/conflict-cherry-pick-feature branches are present.
        self.check_old_commits_unchanged(
            'origin/conflict-cherry-pick-main', 'conflict-cherry-pick-main'
        )
        self.check_old_commits_unchanged(
            'origin/conflict-cherry-pick-feature', 'conflict-cherry-pick-feature'
        )

        # Check the commits count
        self.check_commits_count('conflict-cherry-pick-feature', 8)
        self.check_commits_count('conflict-cherry-pick-main', 6)

        # Check the commit order
        expected_summaries = [
            'Escape the diagram in cheatsheet',
            'Add picture of the basic git workflow',
            'Add commands for working with remote rpositories',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        main_summaries = [
            commit.summary for commit in self.iter_commits('conflict-cherry-pick-main')
        ]
        if main_summaries != expected_summaries:
            raise TaskCheckException(
                'Unexpected commits in conflict-cherry-pick-main branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        print("OK")


class Merge(Task):
    branch_names = ['merge-main', 'merge-feature']

    def start(self):
        self.reset_branches()

        print("""
===========
Task: merge
===========

Merge the `merge-feature` branch into the `merge-main` branch (and create a merge commit in the \
process).

If the history looks like this:

                      A---B feature
                     /
            C---D---E---F main

Then the result should look like this:

                      A---B feature
                     /     \\
            C---D---E---F---G main

The merge commit can contain a message describing the whole feature that was merged.

(To show only task-related branches in gitk: gitk --branches=merge-*)
""")


    def check(self):
        # Check all commits from the origin/merge-main and origin/merge-feature branches are
        # present in merge-main.
        self.check_old_commits_unchanged('origin/merge-main', 'merge-main')
        self.check_old_commits_unchanged('origin/merge-feature', 'merge-main')

        # Check the commits count (old ones, plus one merge commit)
        self.check_commits_count('merge-main', 7)

        # Check last commit is the new merge commit
        last_commit = next(self.iter_commits('merge-main'))

        old_hexshas = []
        old_summaries = []
        for commit in self.iter_commits('origin/merge-main'):
            old_hexshas.append(commit.hexsha)
            old_summaries.append(commit.summary)
        for commit in self.iter_commits('origin/merge-feature'):
            old_hexshas.append(commit.hexsha)
            old_summaries.append(commit.summary)

        if last_commit.hexsha in old_hexshas:
            raise TaskCheckException('The last commit is not new: %s' % last_commit.summary)
        if last_commit.summary in old_summaries:
            raise TaskCheckException(
                'The last commit is probably not new: %s' % last_commit.summary
            )

        print("OK")


class Rebase(Task):
    branch_names = ['rebase-main', 'rebase-feature']

    def start(self):
        self.reset_branches()

        print("""
============
Task: rebase
============

Rebase the `rebase-feature` branch on top of the `rebase-main` branch.

If the history looks like this:

                  A---B feature
                 /
            D---E---F---G main

Then the result should look like this:

                          A'--B' feature
                         /
            D---E---F---G main

(To show only task-related branches in gitk: gitk --branches=rebase-*)
""")


    def check(self):
        # Check all commits from the origin/rebase-main are present in both rebase-main and
        # rebase-feature.
        self.check_old_commits_unchanged('origin/rebase-main', 'rebase-main')
        self.check_old_commits_unchanged('origin/rebase-main', 'rebase-feature')

        # Check the commits count
        self.check_commits_count('rebase-main', 4)
        self.check_commits_count('rebase-feature', 6)

        # Check the commit order
        expected_summaries = [
            'Add explanations to the branching commands',
            'Add basic cheatsheet for working with branches',
            'Add commands for working with remote rpositories',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('rebase-main')]
        if main_summaries != expected_summaries[2:]:
            raise TaskCheckException('The commits in rebase-main branch changed.')

        feature_summaries = [commit.summary for commit in self.iter_commits('rebase-feature')]
        if feature_summaries != expected_summaries:
            raise TaskCheckException(
                'Unexpected commits in rebase-feature branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        print("OK")


class ResetHard(Task):
    branch_names = ['reset-hard-main']

    def start(self):
        self.reset_branches()

        print("""
================
Task: reset-hard
================

Reset the `reset-hard-main` branch to the point right before the last commit. Reset both the \
index and the working tree, i.e. completely discard all changes introduced by the commit.

If the history looks like this:

            A---B---C---D---E---F main

Then the result of resetting to commit B should look like this:

            A---B---C---D---E main

(To show only task-related branches in gitk: gitk --branches=reset-hard-*)
""")


    def check(self):
        # Check all commits from the origin/reset-hard-main are present in reset-hard-main.
        new_hexshas = [commit.hexsha for commit in self.iter_commits('reset-hard-main')]
        new_summaries = [commit.summary for commit in self.iter_commits('reset-hard-main')]
        skip_first = True
        for commit in self.iter_commits('origin/reset-hard-main'):
            if skip_first:
                skip_first = False
                continue
            if commit.hexsha not in new_hexshas:
                if commit.summary not in new_summaries:
                    raise TaskCheckException('A commit is missing: %s' % commit.summary)
                else:
                    raise TaskCheckException(
                        'A commit was unexpectedly modified: %s' % commit.summary
                    )

        # Check the commits count
        self.check_commits_count('reset-hard-main', 5)

        # Check the commit order
        expected_summaries = [
            'Add explanations to the branching commands',
            'Add basic cheatsheet for working with branches',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('reset-hard-main')]
        if main_summaries != expected_summaries:
            raise TaskCheckException(
                'Unexpected commits in reset-hard-main branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        print("OK")


class ResetSoft(Task):
    branch_names = ['reset-soft-main']

    def start(self):
        self.reset_branches()

        print("""
================
Task: reset-soft
================

Reset the `reset-soft-main` branch to the point right before the last commit, but keep the index \
and the working tree.

(To show only task-related branches in gitk: gitk --branches=reset-soft-*)
""")


    def check(self):
        # Check all commits from the origin/reset-soft-main are present in reset-soft-main.
        new_hexshas = [commit.hexsha for commit in self.iter_commits('reset-soft-main')]
        new_summaries = [commit.summary for commit in self.iter_commits('reset-soft-main')]
        skip_first = True
        for commit in self.iter_commits('origin/reset-soft-main'):
            if skip_first:
                skip_first = False
                continue
            if commit.hexsha not in new_hexshas:
                if commit.summary not in new_summaries:
                    raise TaskCheckException('A commit is missing: %s' % commit.summary)
                else:
                    raise TaskCheckException(
                        'A commit was unexpectedly modified: %s' % commit.summary
                    )

        # Check the commits count
        self.check_commits_count('reset-soft-main', 5)

        # Check the commit order
        expected_summaries = [
            'Add explanations to the branching commands',
            'Add basic cheatsheet for working with branches',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('reset-soft-main')]
        if main_summaries != expected_summaries:
            raise TaskCheckException(
                'Unexpected commits in reset-soft-main branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        # Check index
        if self.repo.index.diff(next(self.iter_commits('origin/reset-soft-main'))):
            raise TaskCheckException('The index is not the same as the resetted commit.')

        print("OK")


class Revert(Task):
    branch_names = ['revert-main']

    def start(self):
        self.reset_branches()

        print("""
============
Task: revert
============

In a branch `revert-main`, there is a commit with summary "Make the cheatsheet into a nice table" \
that breaks the markdown in the cheatsheet.md file. Revert this commit.

Note that you don't want to change the history of the `revert-main` branch, but to create new \
commit that is opposite to the one you want to undo.

If the history looks like this:

            A---B---C---D---E---F main

Then the result should look like this:

            A---B---C---D---E---F---D' main

(To show only task-related branches in gitk: gitk --branches=revert-*)
""")


    def check(self):
        # Check all commits from the origin/revert-main are present in revert-main.
        self.check_old_commits_unchanged('origin/revert-main', 'revert-main')

        # Check the commits count
        self.check_commits_count('revert-main', 7)

        # Check the commit order
        expected_summaries = [
            '<REVERT COMMIT>',
            'Add explanations to the branching commands',
            'Add basic cheatsheet for working with branches',
            'Make the cheatsheet into a nice table',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('revert-main')]
        if main_summaries[1:] != expected_summaries[1:]:
            raise TaskCheckException(
                'Unexpected commits in revert-main branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        # Check the last commit is the correct reverted commit by comparing diffs
        commits = [commit for commit in self.iter_commits('revert-main')]
        expected_diffs = commits[4].diff(commits[3], create_patch=True)
        revert_commit_diffs = commits[0].diff(commits[1], create_patch=True)
        if revert_commit_diffs != expected_diffs:
            expected_patch = '\n'.join([diff.diff.decode('utf8') for diff in expected_diffs])
            actual_patch = '\n'.join([diff.diff.decode('utf8') for diff in revert_commit_diffs])
            raise TaskCheckException(
                'The last commit is not the reverted commit.\n\n'
                'Expected diff:\n\n%s\nActual diff:\n\n%s' % (expected_patch, actual_patch))

        print("OK")

class ChangeMessage(Task):
    branch_names = ["change-message-tasks"]

    def start(self):
        self.reset_branches()

        print("""
====================
Task: change-message
====================

In a branch `change-message-tasks`, there are several commits that make up a complete poem by \
Emily Dickinson. The very first commit of the branch has a wrong commit message saying \
`Add title and author`. 

Use interactive rebase to replace the commit message, so that the new message is `Add 'After Great Pain' by Emily Dickinson.`

Make sure that the commit history remains unchanged, except for this one commit message.

""")

    def check(self):
        # Check the commits count
        self.check_commits_count('change-message-tasks', 2)

        # Check the commit order
        expected_summaries = [
            'Add text.',
            "Add 'After Great Pain' by Emily Dickinson.",
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('change-message-tasks')]
        if len(main_summaries) != len(expected_summaries):
            raise TaskCheckException(
                'The number of new commits in change-message-main branch differs from the '
                'expected number. Expected commit number: %s' % (len(expected_summaries))
            )

        # Check that the commit message has been changed.
        if main_summaries[1] != expected_summaries[1]:
            raise TaskCheckException(
                'The commit message seems not be changed correctly.\nCurrent message: '
                '%s\nExpected message: %s' % (main_summaries[1], expected_summaries[1]))

        print("OK")


class SquashCommit(Task):
    branch_names = ["squash-commits-tasks"]

    def start(self):
        self.reset_branches()

        print("""
====================
Task: squash-commits
====================

In a branch `squash-commits-tasks`, there are several commits that make up a complete poem by \
Emily Dickinson. Before we merge the content of this branch into `main`, we would like to squash \
the commits so that the whole added content is only represented by \
the very first commit. All following commits should be squashed into the first one. 

Use interactive rebase to squash the commits, so that there is only the very first commit left in \
the branch, while the content of the branch remains unchanged.

""")

    def check(self):

        # Check the commits count
        self.check_commits_count('squash-commits-tasks', 1)

        # Check the commit order.
        expected_summaries = [
            "Add 'Fame is a bee' by Emily Dickinson.",
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('squash-commits-tasks')]
        if len(main_summaries) != len(expected_summaries):
            raise TaskCheckException(
                'The number of new commits in squash-commits-tasks branch differs from the '
                'expected number. Expected commit number: %s' % (len(expected_summaries))
            )

        if main_summaries[0] != "Add 'Fame is a bee' by Emily Dickinson.":
            raise TaskCheckException(
                'The message of the first commit has changed, but it should be the same.\n'
                'Expected commit message: %s\nCurrent commit message: %s' % (
                    expected_summaries[0], main_summaries[0]
                )
             )

        # Check that there is no difference in content between the original and the squashed
        # repository.
        original = [commit for commit in self.iter_commits('origin/squash-commits-tasks')]
        new = [commit for commit in self.iter_commits('squash-commits-tasks')]

        diff = original[0].diff(new[0], create_patch=True)

        if diff:
            raise TaskCheckException(
                'The content of the squashed branch is different from the original branch.\n'
                'See the diff: \n%s' % diff[0])

        print("OK")

class ReorganizeCommits(Task):
    branch_names = ["reorganize-commits-tasks"]

    def start(self):
        self.reset_branches()

        print("""
========================
Task: reorganize-commits
========================

In a branch `reorganize-commits-tasks`, there are several commits that make up two complete poems \
by Emily Dickinson. Before we merge the content of this branch into `main`, we would like to \
squash the commits so that the whole added content is only represented by two commits, each one \
for a particular poem.  

Use interactive rebase to reorganize, squash and reword the commits, so that there are only two \
commits left in the branch, while the content of the branch remains unchanged.

The final commits should be named `Poem 1: Add a poem.` and `Poem 2: Add a poem.`

""")

    def check(self):

        # Check the commits count
        self.check_commits_count('reorganize-commits-tasks', 2)

        # Check the commit order.
        expected_summaries = [
            "Poem 2: Add a poem.",
            "Poem 1: Add a poem.",
        ]

        main_summaries = [
            commit.summary for commit in self.iter_commits('reorganize-commits-tasks')
        ]
        if len(main_summaries) != len(expected_summaries):
            raise TaskCheckException(
                'The number of new commits in this branch differs from the expected number.'
                'Expected commit number: %s' % (len(expected_summaries))
            )

        if main_summaries[0] != "Poem 2: Add a poem.":
            raise TaskCheckException(
                'The message of the second commit differs from what is expected.\n'
                'Expected commit message: %s\nCurrent commit message: %s' % (
                    expected_summaries[0], main_summaries[0]
                )
             )

        if main_summaries[1] != "Poem 1: Add a poem.":
            raise TaskCheckException(
                'The message of the first commit differs from what is expected.\n'
                'Expected commit message: %s\nCurrent commit message: %s' % (
                    expected_summaries[1], main_summaries[1]
                )
             )

        # Check that there is no difference in content between the original and the squashed
        # repository.
        original = [commit for commit in self.iter_commits('origin/reorganize-commits-tasks')]
        new = [commit for commit in self.iter_commits('reorganize-commits-tasks')]

        diff = original[0].diff(new[0], create_patch=True)

        if diff:
            raise TaskCheckException(
                'The content of the squashed branch is different from the original branch.\n'
                'See the diff: \n%s' % diff[0])

        print("OK")


class CommitAmend(Task):
    branch_names = ["commit-amend-tasks"]

    def start(self):
        self.reset_branches()

        print("""
==================
Task: commit-amend
==================

In the branch `commit-amend-tasks`, there is one commit that makes up a complete poem by Emily \
Dickinson. Unfortunately, one of the writers made a typo and left this mistake in the name of \
the author which is `Elimy` but should be `Emily`. Before we merge the content of this branch \
into `main`, we would like to correct the mistake before we do so.   

Since this is only a minor change and we have already squashed all the commits in the branch, do \
not produce an extra commit, but add the change to the existing commit instead. 

After the change, there should be one commit only in the branch with the same commit message as \
before!

""")

    def check(self):

        # Check the commits count
        self.check_commits_count('commit-amend-tasks', 1)

        # Check the commit order.
        expected_summaries = [
            "Add poem: Forever is composed of nows",
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('commit-amend-tasks')]
        if len(main_summaries) != len(expected_summaries):
            raise TaskCheckException(
                'The number of new commits in this branch differs from the expected number.'
                'Expected commit number: %s' % (len(expected_summaries))
            )

        if main_summaries[0] != "Add poem: Forever is composed of nows":
            raise TaskCheckException(
                'The message of the commit differs from what is expected.\n'
                'Expected commit message: %s\nCurrent commit message: %s' % (
                    expected_summaries[0], main_summaries[0]
                )
             )

        # Check that there is a difference in content between the original and the new commit.
        original = [commit for commit in self.iter_commits('origin/commit-amend-tasks')]
        new = [commit for commit in self.iter_commits('commit-amend-tasks')]

        diff = original[0].diff(new[0], create_patch=True)
        detail = str(diff[0].diff)

        if not diff:
            raise TaskCheckException(
                'The content of the branch seems not to be corrected! '
                'The text is the same as it was before.\n')
        else:
            if "+*By Emily Dickinson*" not in detail:
                raise TaskCheckException(
                    'The mistake was not corrected as expected.\n\n'
                    'See the diff:\n%s' % diff[0])

        print("OK")

class Stash(Task):
    branch_names = ["stash-tasks"]

    def start(self):
        self.reset_branches()

        print("""
===========
Task: stash
===========

In the branch `stash-tasks`, there is one commit that makes up a skeleton for your own poem. You \
should change the skeleton file into a text of your liking. Change some lines and save the file.

Unfortunately, before you could commit and push the changes, you have learnt that the remote \
branch has been rebased and you need to reset your local branch to the remote branch, but you do \
not want to lose any changes you have already made in your local branch.

Use stash to protect your changes and reset local branch onto the remote one.

""")

    def check(self):

        # Check the commits count
        self.check_commits_count('stash-tasks', 1)

        # Check the commit order.
        expected_summaries = [
            "Add a poem skeleton.",
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('stash-tasks')]
        if len(main_summaries) != len(expected_summaries):
            raise TaskCheckException(
                'The number of commits in this branch differs from the expected number. Reset the '
                'branch. Expected commit number: %s' % (len(expected_summaries))
            )

        if main_summaries[0] != "Add a poem skeleton.":
            raise TaskCheckException(
                'The message of the commit differs from what is expected. Reset the branch.\n'
                'Expected commit message: %s\nCurrent commit message: %s' % (
                    expected_summaries[0], main_summaries[0]
                )
             )

        # Check that there is a difference in content between the original and the new commit.
        original = [commit for commit in self.iter_commits('origin/stash-tasks')]
        new = [commit for commit in self.iter_commits('stash-tasks')]

        # Check that there is a stash saved.
        direct = self.repo.git
        stash = direct.stash('list')

        if not stash:
            raise TaskCheckException(
                'Nothing has been put into stash. The content is not protected.\n\n'
                'Expected was something like "stash@{0}: WIP on stash-tasks: ..."')

        print("OK")


class ApplyStash(Task):
    branch_names = ["apply-stash-tasks"]

    def start(self):
        self.reset_branches()

        print("""
=================
Task: apply-stash
=================

In the branch `apply-stash-tasks`, there is one commit that makes up a skeleton for your own \
poem. You should change the skeleton file into a text of your liking. Change some lines and save \
    the file.

Unfortunately, before you could commit and push the changes, you have learnt that the remote \
branch has been rebased and you need to reset your local branch to the remote branch, but you do \
not want to lose any changes you have already made in your local branch.

Use stash to protect your changes and reset local branch onto the remote one. Then apply the \
stashed content and delete it from the stash. Stage the new content and commit it. Make the \
commit message be 'Add my favourite poem.'

""")

    def check(self):

        # Check the commits count
        self.check_commits_count('apply-stash-tasks', 2)

        # Check the commit order.
        expected_summaries = [
            "Add my favourite poem.",
            "Add a poem skeleton.",
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('apply-stash-tasks')]
        if len(main_summaries) != len(expected_summaries):
            raise TaskCheckException(
                'The number of commits in this branch differs from the expected number.'
                'Expected commit number: %s' % (len(expected_summaries))
            )

        if main_summaries[0] != "Add my favourite poem.":
            raise TaskCheckException(
                'The message of the commit differs from what is expected.\n'
                'Expected commit message: %s\nCurrent commit message: %s' % (
                    expected_summaries[0], main_summaries[0]
                )
             )

        # Check that there is a difference in content between the original and the new commit.
        original = [commit for commit in self.iter_commits('origin/apply-stash-tasks')]
        new = [commit for commit in self.iter_commits('apply-stash-tasks')]

        diff = original[0].diff(new[0], create_patch=True)

        if not diff:
            raise TaskCheckException(
                'The content of the branch seems not to be correctly applied from stash!')

        # Check that there is a stash saved.
        direct = self.repo.git
        stash = direct.stash('list')

        if stash:
            raise TaskCheckException(
                'There is something in the stash, but the stash should be empty.\n\n'
                'See stash:\n%s' % stash)

        print("OK")


class ConflictRevert(Task):
    branch_names = ['conflict-revert-main']

    def start(self):
        self.reset_branches()

        print("""
=====================
Task: conflict-revert
=====================

In a branch `conflict-revert-main`, there is a commit with summary "Make the cheatsheet into a \
nice table" that breaks the markdown in the cheatsheet.md file. Revert this commit.

Note that you don't want to change the history of the `conflict-revert-main` branch, but to \
create new commit that is opposite to the one you want to undo.

In this scenario, you will encounter a conflict and will need to resolve it.

If the history looks like this:

            A---B---C---D---E---F---G main

Then the result should look like this:

            A---B---C---D---E---F---D' main

(To show only task-related branches in gitk: gitk --branches=conflict-revert-*)
""")


    def check(self):
        # Check all commits from the origin/conflict-revert-main are present in
        # conflict-revert-main.
        self.check_old_commits_unchanged('origin/conflict-revert-main', 'conflict-revert-main')

        # Check the commits count
        self.check_commits_count('conflict-revert-main', 8)

        # Check the commit order
        expected_summaries = [
            '<REVERT COMMIT>',
            'Add picture of the basic git workflow',
            'Add explanations to the branching commands',
            'Add basic cheatsheet for working with branches',
            'Make the cheatsheet into a nice table',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('conflict-revert-main')]
        if main_summaries[1:] != expected_summaries[1:]:
            raise TaskCheckException(
                'Unexpected commits in conflict-revert-main branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        # Check the last commit is the correct reverted commit
        expected_lines = [
            'Git Cheatsheet',
            '==============',
            '- git add     - add file contents to the index',
            '- git commit  - record changes to the repository',
            '```',
            '+-----------+          +---------+             +------------+',
            '|  working  | -------> | staging | ----------> | repository |',
            '| directory | git add  |  area   | git commit  |            |',
            '+-----------+          +---------+             +------------+',
            '```',
            '- git status  - show the working tree status',
            '- git log     - show commit logs',
            '- git show    - show various types of objects',
        ]
        self.repo.git.checkout('conflict-revert-main')
        with open('source/cheatsheet.md') as f:
            lines = [line.strip() for line in f if line.strip()]
        if lines != expected_lines:
            raise TaskCheckException(
                'The content of source/cheatsheet.md is different than expected. '
                'Expected lines (without empty lines):\n%s' % '\n'.join(expected_lines)
            )

        print("OK")


class NewBranch(Task):
    branch_names = ['new-branch-main']

    def start(self):
        self.reset_branches()

        print("""
================
Task: new-branch
================

Find a commit in branch `new-branch-main` with a summary "Add commands for working with remote \
rpositories".

Create a new branch named `new-branch` on this commit.
""")


    def check(self):
        # Check branch exists
        if 'new-branch' not in self.repo.references:
            raise TaskCheckException('Branch "new-branch" does not exist.')

        # Check all commits from the origin/new-branch-main branch are present.
        self.check_old_commits_unchanged('origin/new-branch-main', 'new-branch-main')

        # Check the commits count
        self.check_commits_count('new-branch-main', 6)
        self.check_commits_count('new-branch', 4)

        # Check the commit order
        expected_summaries = [
            'Add commands for working with remote rpositories',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        summaries = [commit.summary for commit in self.iter_commits('new-branch')]
        if summaries != expected_summaries:
            raise TaskCheckException(
                'Unexpected commits in new-branch branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        self.check_old_commits_unchanged('new-branch', 'new-branch-main')

        print("OK")


class Drop(Task):
    branch_names = ['drop-main']

    def start(self):
        self.reset_branches()

        print("""
==========
Task: drop
==========

In a branch `drop-main`, there is a commit with summary "Make the cheatsheet into a nice table" \
that breaks the markdown in the cheatsheet.md file.

Using an interactive rebase, drop this commit.

If the history looks like this:

            A---B---C---D---E---F main

Then the result should look like this:

            A---B---C---E---F main

(To show only task-related branches in gitk: gitk --branches=drop-*)
""")


    def check(self):
        # Check the commits count
        self.check_commits_count('drop-main', 5)

        # Check the commit order
        expected_summaries = [
            'Add explanations to the branching commands',
            'Add basic cheatsheet for working with branches',
            'Add explanations to individual commands',
            'Add commands for inspecting the repo',
            'Add cheatsheet with basic git commands',
        ]

        main_summaries = [commit.summary for commit in self.iter_commits('drop-main')]
        if main_summaries != expected_summaries:
            raise TaskCheckException(
                'Unexpected commits in drop-main branch. '
                'Expected summaries:\n%s' % '\n'.join(expected_summaries)
            )

        print("OK")


class Blame(Task):
    branch_names = ['blame-main']

    def start(self):
        self.reset_branches()

        print("""
===========
Task: blame
===========

In a branch `blame-main`, who last changed the line 78 in the file `source/cheatsheet.md`?

Who originally introduced the typo in the word "download"?

(To show only task-related branches in gitk: gitk --branches=blame-*)
""")

    def check(self):
        print("Nothing to check.")


class Add(Task):
    branch_names = ['simple']

    def start(self):
        self.reset_branches()

        print("""
=========
Task: add
=========

Switch to a branch named `simple`.

Then create two new files named "day" and "night" and add the "day" file to the index.
""")

    def check(self):
        # Check the commits count
        self.check_commits_count('simple', 11)

        # Check all commits from the origin/simple branch are present.
        self.check_old_commits_unchanged('origin/simple', 'simple')

        # Check index
        staged = [item.a_path for item in self.repo.index.diff('HEAD')]
        if len(staged) != 1 or 'day' not in staged:
            raise TaskCheckException(
                'There are different paths in index that expected. It should contain only '
                'the "day" file. List of staged files: %s' % ', '.join(staged))

        # Check untracked files
        untracked = self.repo.untracked_files
        if 'night' not in untracked:
            raise TaskCheckException(
                'The "night" file should be untracked, but is not. List of untracked '
                'files: %s' % ', '.join(untracked))

        print("OK")


class Commit(Task):
    branch_names = ['simple']

    def start(self):
        self.reset_branches()

        print("""
============
Task: commit
============

Switch to a branch named `simple`.

Then create a new file named "new-file" and commit it.
""")

    def check(self):
        # Check the commits count
        self.check_commits_count('simple', 12)

        # Check all commits from the origin/simple branch are present.
        self.check_old_commits_unchanged('origin/simple', 'simple')

        # Check the last commit contains only the one changed file
        commit = next(self.iter_commits('simple'))
        changed_files = commit.stats.files.keys()
        if not changed_files:
            raise TaskCheckException(
                'The "new-file" file is not in the commit. '
                'There are no files changed by the commit.')
        if 'new-file' not in changed_files:
            raise TaskCheckException(
                'The "new-file" file is not in the commit. List of files changed by the '
                'commit: %s' % ', '.join(changed_files))
        if len(changed_files) > 1:
            raise TaskCheckException(
                'There are too many files changed by the commit: %s' % ', '.join(changed_files))

        print("OK")


class Switch(Task):
    branch_names = ['simple']

    def start(self):
        self.reset_branches()

        print("""
============
Task: switch
============

Switch to a branch named "simple".
""")

    def check(self):
        # Check current branch is "simple"
        if self.repo.active_branch.name != 'simple':
            raise TaskCheckException(
                'Current branch is not "simple", but "%s".' % self.repo.active_branch.name)
        
        # Check the commits count
        self.check_commits_count('simple', 11)

        # Check all commits from the origin/simple branch are present.
        self.check_old_commits_unchanged('origin/simple', 'simple')

        print("OK")


class Log(Task):
    branch_names = ['simple']

    def start(self):
        self.reset_branches()

        print("""
=========
Task: log
=========

In a branch `simple`, who made the last but one commit?

What is the summary of the last but one commit?

What is the second changed line in the last but one commit?
""")

    def check(self):
        print("Nothing to check.")


class Diff(Task):
    branch_names = ['diff-one', 'diff-two']

    def start(self):
        self.reset_branches()

        print("""
==========
Task: diff
==========

What is the difference between `diff-one` and `diff-two` branches?
""")

    def check(self):
        print("Nothing to check.")


def main():
    # Define tasks:
    task_classes = {
        'cherry-pick': CherryPick,
        'conflict-cherry-pick': ConflictCherryPick,
        'merge': Merge,
        'rebase': Rebase,
        'reset-hard': ResetHard,
        'reset-soft': ResetSoft,
        'revert': Revert,
        'conflict-revert': ConflictRevert,
        'change-message': ChangeMessage,
        'squash-commits': SquashCommit,
        'reorganize-commits': ReorganizeCommits,
        'commit-amend': CommitAmend,
        'stash': Stash,
        'apply-stash': ApplyStash,
        'new-branch': NewBranch,
        'drop': Drop,
        'blame': Blame,
        'add': Add,
        'commit': Commit,
        'switch': Switch,
        'log': Log,
        'diff': Diff,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('taskname', help='Name of a task')
    parser.add_argument('command', choices=['start', 'check'], help='Command to run')
    args = parser.parse_args()

    if args.taskname not in task_classes:
        raise TaskException('Task "%s" not found.' % args.taskname)

    task = task_classes[args.taskname]()
    func = getattr(task, args.command, None)
    if not callable(func):
        raise TaskException(
            'Command "%s" for task "%s" not found.' % (args.command, args.taskname)
        )
    func()


if __name__ == "__main__":
    try:
        main()
    except TaskException as e:
        print(e)
        sys.exit(1)
