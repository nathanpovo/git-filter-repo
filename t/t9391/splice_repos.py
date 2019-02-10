#!/usr/bin/env python

import re
import sys
import git_filter_repo as fr

class InterleaveRepositories:
  def __init__(self, repo1, repo2, output_dir):
    self.repo1 = repo1
    self.repo2 = repo2
    self.output_dir = output_dir

    self.commit_map = {}
    self.last_commit = None

  def skip_reset(self, reset):
    reset.skip()

  def hold_commit(self, commit):
    commit.skip(new_id = commit.id)
    letter = re.match('Commit (.)', commit.message).group(1)
    self.commit_map[letter] = commit

  def weave_commit(self, commit):
    letter = re.match('Commit (.)', commit.message).group(1)
    prev_letter = chr(ord(letter)-1)

    # Splice in any extra commits needed
    if prev_letter in self.commit_map:
      new_commit = self.commit_map[prev_letter]
      new_commit.from_commit = self.last_commit
      new_commit.dump(self.out._output)
      commit.from_commit = new_commit.id

    # Dump our commit now
    commit.dump(self.out._output)

    # Make sure that commits that depended on new_commit.id will now depend
    # on commit.id
    if prev_letter in self.commit_map:
      self.last_commit = commit.id
      fr.record_id_rename(new_commit.id, commit.id)

  def run(self):
    blob = fr.Blob('public gpg key contents')
    tag = fr.Tag('gpg-pubkey', blob.id,
                 'Ima Tagger', 'ima@tagg.er', '1136199845 +0300',
                 'Very important explanation and stuff')

    args = fr.FilteringOptions.parse_args(['--target', self.output_dir])
    out = fr.RepoFilter(args)
    out.importer_only()
    self.out = out

    i1args = fr.FilteringOptions.parse_args(['--source', self.repo1])
    i1 = fr.RepoFilter(i1args,
                                reset_callback  = lambda r: self.skip_reset(r),
                                commit_callback = lambda c: self.hold_commit(c))
    i1.set_output(out)
    i1.run()

    i2args = fr.FilteringOptions.parse_args(['--source', self.repo2])
    i2 = fr.RepoFilter(i2args,
                                commit_callback = lambda c: self.weave_commit(c))
    i2.set_output(out)
    i2.run()

    blob.dump(out._output)
    tag.dump(out._output)
    out.finish()

splicer = InterleaveRepositories(sys.argv[1], sys.argv[2], sys.argv[3])
splicer.run()
