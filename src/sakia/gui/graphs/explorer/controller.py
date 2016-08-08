from ..base.controller import BaseGraphController
from sakia.tools.decorators import asyncify, once_at_a_time
from .view import ExplorerView
from .model import ExplorerModel


class ExplorerController(BaseGraphController):
    """
    The homescreen view
    """

    def __init__(self, parent, view, model, password_asker=None):
        """
        Constructor of the explorer component

        :param sakia.gui.graphs.explorer.view.ExplorerView: the view
        :param sakia.gui.graphs.explorer.model.ExplorerModel model: the model
        """
        super().__init__(parent, view, model, password_asker)
        self.set_scene(view.scene())
        self.reset()
        self.view.button_go.clicked.connect(lambda checked: self.refresh())

    @property
    def view(self) -> ExplorerView:
        return self._view

    @property
    def model(self) -> ExplorerModel:
        return self._model

    @classmethod
    def create(cls, parent, app, **kwargs):
        account = kwargs['account']
        community = kwargs['community']

        view = ExplorerView(parent.view)
        model = ExplorerModel(None, app, account, community)
        wot = cls(parent, view, model)
        model.setParent(wot)
        return wot

    async def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param sakia.core.registry.Identity identity: Center identity
        """
        await self.model.set_identity(identity)
        self.model.graph.start_exploration(self.model.identity, self.view.steps())

        # draw graph in qt scene
        self.view.scene().clear()
        self.view.update_wot(self.model.graph.nx_graph, self.model.identity)

    @once_at_a_time
    @asyncify
    async def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        self.model.graph.stop_exploration()
        await self.draw_graph(self.model.identity)
        self.view.update_wot(self.model.graph.nx_graph, self.model.identity)

    @once_at_a_time
    @asyncify
    async def reset(self, checked=False):
        """
        Reset graph scene to wallet identity
        """
        self.view.reset_steps()
        maximum_steps = await self.model.maximum_steps()
        self.view.set_steps_max(maximum_steps)
        await self.draw_graph(None)
