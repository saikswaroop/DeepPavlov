"""
Copyright 2017 Neural Networks and Deep Learning lab, MIPT

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
from overrides import overrides

import numpy as np

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from deeppavlov.core.common.log import get_logger
from deeppavlov.core.models.serializable import Serializable

log = get_logger(__name__)


@register('fasttext')
class FasttextEmbedder(Component, Serializable):
    def __init__(self, load_path, save_path=None, dim=100,
                 emb_module='fasttext', **kwargs):
        super().__init__(save_path=save_path,
                         load_path=load_path)
        self.tok2emb = {}
        self.dim = dim
        self.emb_module = emb_module
        self.model = self.load()

    def save(self, *args, **kwargs):
        raise NotImplementedError

    def load(self, *args, **kwargs):
        """
        Load dict of embeddings from file
        """

        if self.load_path and self.load_path.is_file():
            log.info("[loading embeddings from `{}`]".format(self.load_path))
            model_file = str(self.load_path)
            if self.emb_module == 'fasttext':
                import fasttext as Fasttext
                model = Fasttext.load_model(model_file)
            elif self.emb_module == 'pyfasttext':
                from pyfasttext import FastText as Fasttext
                model = Fasttext(model_file)
            else:
                from gensim.models.wrappers.fasttext import FastText as Fasttext
                model = Fasttext.load_fasttext_format(model_file)
        else:
            log.error('No pretrained fasttext model provided or provided load_path "{}" is incorrect.'
                      .format(self.load_path))
            sys.exit(1)

        return model

    @overrides
    def __call__(self, batch, mean=False, *args, **kwargs):
        """
        Embed data
        """
        return [self._encode(sentence, mean) for sentence in batch]

    def _encode(self, sentence: str, mean):
        tokens = sentence.split()
        embedded_tokens = []
        for t in tokens:
            try:
                emb = self.tok2emb[t]
            except KeyError:
                try:
                    emb = self.model[t][:self.dim]
                except KeyError:
                    emb = np.zeros(self.dim, dtype=np.float32)
                self.tok2emb[t] = emb
            embedded_tokens.append(emb)

        if mean:
            filtered = [et for et in embedded_tokens if np.any(et)]
            if filtered:
                return np.mean(filtered, axis=0)
            return np.zeros(self.dim, dtype=np.float32)

        return embedded_tokens
