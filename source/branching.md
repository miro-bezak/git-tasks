How to work in branches
=======================

- git branch  - list, create, or delete branches
- git switch  - switch branches

- git merge   - join two or more development histories together

  - Before merge:
```
            A---B---C topic
           /
      D---E---F---G master
```

  - After merge:
```
            A---B---C topic
           /         \
      D---E---F---G---H master
```

- git rebase  - reapply commits on top of another base tip
nother base tip
 
  - Before rebase:
```
            A---B---C topic
           /
      D---E---F---G master
```

  - After rebase:
```
                    A'--B'--C' topic
                   /
      D---E---F---G master
```

