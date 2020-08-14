from tensorflow.keras import optimizers
from tensorflow.keras.layers import Dense

from pipeline.backend.config import Backend
from pipeline.backend.config import WorkMode
from pipeline.backend.pipeline import PipeLine
from pipeline.component.dataio import DataIO
from pipeline.component.hetero_nn import HeteroNN
from pipeline.component.input import Input
from pipeline.component.intersection import Intersection
from pipeline.interface.data import Data
from pipeline.interface.model import Model

guest = 9999
hosts = [10000]

guest_train_data = {"name": "breast_hetero_guest", "namespace": "experiment"}
host_train_data = [{"name": "breast_hetero_host", "namespace": "experiment"}]

input_0 = Input(name="train_data")
print("get input_0's init name {}".format(input_0.name))

pipeline = PipeLine().set_initiator(role='guest', party_id=9999).set_roles(guest=9999, host=hosts)
dataio_0 = DataIO(name="dataio_0")

dataio_0.get_party_instance(role='guest', party_id=guest).algorithm_param(with_label=True, output_format="dense")
dataio_0.get_party_instance(role='host', party_id=hosts).algorithm_param(with_label=False)

intersection_0 = Intersection(name="intersection_0")
hetero_nn_0 = HeteroNN(name="hetero_nn_0", epochs=10)
hetero_nn_0.add_bottom_model(Dense(units=2, input_shape=(10,), activation="relu"))
hetero_nn_0.set_interactve_layer(Dense(units=2, input_shape=(2,), activation="relu"))
hetero_nn_0.add_top_model(Dense(units=1, input_shape=(2,), activation="sigmoid"))
hetero_nn_0.compile(optimizer=optimizers.SGD(lr=0.1), metrics=["AUC"], loss="binary_crossentropy")
hetero_nn_1 = HeteroNN(name="hetero_nn_1")

print("get input_0's name {}".format(input_0.name))
pipeline.add_component(dataio_0, data=Data(data=input_0.data))
pipeline.add_component(intersection_0, data=Data(data=dataio_0.output.data))
pipeline.add_component(hetero_nn_0, data=Data(train_data=intersection_0.output.data))
pipeline.add_component(hetero_nn_1, data=Data(test_data=intersection_0.output.data),
                       model=Model(model=hetero_nn_0.output.model))

pipeline.compile()

pipeline.fit(backend=Backend.EGGROLL, work_mode=WorkMode.STANDALONE,
             feed_dict={input_0:
                            {"guest": {9999: guest_train_data},
                             "host": {
                                 10000: host_train_data[0]
                             }
                             }

                        })

pipeline.deploy_component([dataio_0, hetero_nn_0])
print(pipeline.get_component("hetero_nn_0").get_output_data())

# predict

pipeline.predict(backend=Backend.EGGROLL, work_mode=WorkMode.STANDALONE,
                 feed_dict={input_0:
                                {"guest":
                                     {9999: guest_train_data},
                                 "host": {
                                     10000: host_train_data[0]
                                 }
                                 }
                            })

with open("output.pkl", "wb") as fout:
    fout.write(pipeline.dump())