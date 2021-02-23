# just a collection of misc stuff #

* tmux.conf: make tmux behave like screen (may be incomplete); also tmux.confs
  get outdated rather often, so this one may not be suitable for arbitrary tmux
  versions
* edit_commit_files: edit all files of a given commit along with the diff; if
  no commit was given and files have modified (yet not staged), those files
  will be loaded, without local changes HEAD will be used; the temporary diff
  file will be deleted after the editor is closed;
