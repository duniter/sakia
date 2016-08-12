from ..base.controller import BaseGraphController
from sakia.tools.decorators import asyncify, once_at_a_time
from .view import ExplorerView
from .model import ExplorerModel
from ...search_user.controller import SearchUserController
import asyncio


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
        self.view.button_go.clicked.connect(self.start_exploration)
        self.model.graph.graph_changed.connect(self.refresh)
        self.model.graph.current_identity_changed.connect(self.view.update_current_identity)

    def center_on_identity(self, identity):
        """
        Draw community graph centered on the identity

        :param sakia.core.registry.Identity identity: Center identity
        """
        asyncio.ensure_future(self.draw_graph(identity))

    def start_exploration(self):
        self.model.graph.stop_exploration()
        self.model.graph.start_exploration(self.model.identity, self.view.steps())

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
        explorer = cls(parent, view, model)
        model.setParent(explorer)
        search_user = SearchUserController.create(explorer, app, **{'account': account,
                                                                    'community': community})
        explorer.view.set_search_user(search_user.view)
        search_user.identity_selected.connect(explorer.center_on_identity)
        return explorer

    async def draw_graph(self, identity):
        """
        Draw community graph centered on the identity

        :param sakia.core.registry.Identity identity: Center identity
        """
        self.view.update_wot(self.model.graph.nx_graph, identity)

    @once_at_a_time
    @asyncify
    async def refresh(self):
        """
        Refresh graph scene to current metadata
        """
        await self.draw_graph(self.model.identity)
        self.view.update_wot(self.model.graph.nx_graph, self.model.identity)

    @once_at_a_time
    @asyncify
    async def reset(self, checked=False):
        """
        Reset graph scene to wallet identity
        """
        # draw graph in qt scene
        self.view.scene().clear()
        self.view.reset_steps()
        maximum_steps = await self.model.maximum_steps()
        self.view.set_steps_max(maximum_steps)
        await self.model.set_identity(None)
        await self.draw_graph(self.model.identity)
