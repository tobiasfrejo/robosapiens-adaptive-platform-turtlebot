use futures::StreamExt;
use futures::stream::BoxStream;
use paho_mqtt as mqtt;
use paho_mqtt::Message;
use r2r;
use r2r::builtin_interfaces::msg::Time;
use r2r::Publisher;
use r2r::QosProfile;
use r2r::qos::DurabilityPolicy as QosDurabilityPolicy;
use r2r::qos::HistoryPolicy as QosHistoryPolicy;
use r2r::qos::ReliabilityPolicy as QosReliabilityPolicy;
use r2r::spin_interfaces::msg::SpinPeriodicCommands as MSpinCommands;
use r2r::geometry_msgs::msg::PoseStamped as MPoseStamped;
use serde::Deserialize;
use serde::Serialize;
use tokio::select;
use tokio::sync::oneshot;
use tracing::info;
// Removed incorrect import of std::fmt::Result.
use serde::de::{self, Deserializer};
use serde_json::Value;
use std::f64::consts::PI;
use std::time::Duration;
use tracing::debug;
use tracing::error;
use tracing::instrument;
use tracing::warn;
use uuid::Uuid;

const MQTT_QOS: i32 = 1;
pub const SCAN_TOPIC: Topic = Topic {
    ros_name: "/scan_safe",
    mqtt_name: "/Scan",
};
pub const SPIN_TOPIC: Topic = Topic {
    ros_name: "/spin_config",
    mqtt_name: "/spin_config",
};

pub const COLLISION_TOPIC: Topic = Topic {
    ros_name: "/cmd_vel_monitor",
    mqtt_name: "CollisionDetect"
};
pub const VELOCITY_TOPIC: Topic = Topic {
    ros_name: "/cmd_vel",
    mqtt_name: "NormalVelocity"
};

pub const ODOM_TOPIC: Topic = Topic {
    ros_name: "/odom",
    mqtt_name: "Odometry"
};

pub const GOAL_TOPIC: Topic = Topic {
    ros_name: "/goal_pose",
    mqtt_name: "/goal_pose"
};


pub const TOPICS: [Topic; 6] = [SCAN_TOPIC, SPIN_TOPIC, COLLISION_TOPIC, VELOCITY_TOPIC, ODOM_TOPIC, GOAL_TOPIC];

#[derive(Clone)]
pub struct Topic {
    pub ros_name: &'static str,
    pub mqtt_name: &'static str,
}
impl Copy for Topic {}

impl Topic {
    #[allow(dead_code)]
    fn ros_topic(topic: &str) -> Option<Topic> {
        TOPICS.iter().cloned().find(|&x| x.ros_name == topic)
    }

    #[allow(dead_code)]
    fn mqtt_topic(topic: &str) -> Option<Topic> {
        TOPICS.iter().cloned().find(|&x| x.mqtt_name == topic)
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
#[serde(untagged)]
enum ROS2MQTTData {
    LaserScan(r2r::sensor_msgs::msg::LaserScan),
    Twist(r2r::geometry_msgs::msg::Twist),
    Odometry(r2r::nav_msgs::msg::Odometry),
}

#[derive(Serialize, Debug, Clone)]
#[serde(untagged)]
enum MQTT2ROSData {
    SpinCommands(MSpinCommands),
    PoseStamped(MPoseStamped)
}

/* Implement a custom deserializer for MQTT2ROSData
 * This added stricter validation than the default derived one, which does not
 * check for the presence of required fields in the SpinCommands message and
 * allows for extra fields.
 */
impl<'de> Deserialize<'de> for MQTT2ROSData {
    fn deserialize<D>(deserializer: D) -> Result<MQTT2ROSData, D::Error>
    where
        D: Deserializer<'de>,
    {
        let value = Value::deserialize(deserializer)?;

        // Try SpinCommandsHelper
        if value.get("commands").is_some() && value.get("period").is_some() {
            let helper: SpinCommandsHelper = serde_json::from_value(value.clone())
                .map_err(de::Error::custom)?;
            let spin_cmds = MSpinCommands::try_from(helper)
                .map_err(de::Error::custom)?;
            return Ok(MQTT2ROSData::SpinCommands(spin_cmds));
        }

        // Try PoseHelper
        if value.get("position").is_some() && value.get("orientation").is_some() {
            let helper: PoseHelper = serde_json::from_value(value.clone())
                .map_err(de::Error::custom)?;
            let pose = MPoseStamped::try_from(helper)
                .map_err(de::Error::custom)?;
            return Ok(MQTT2ROSData::PoseStamped(pose));
        }

        Err(de::Error::custom("Invalid structure for MQTT2ROSData"))

        // // Deserialize into the helper struct. This will enforce that exactly
        // // the fields "commands" (an array of objects each with "omega" and "duration")
        // // and "period" are present.
        // let helper = SpinCommandsHelper::deserialize(deserializer).map_err(de::Error::custom)?;
        // // Convert the helper to your ROS message type.
        // let spin_cmds = MSpinCommands::try_from(helper).map_err(de::Error::custom)?;
        // Ok(MQTT2ROSData::SpinCommands(spin_cmds))
    }
}

// A helper struct for individual spin commands.
#[derive(Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct SpinCommandHelper {
    omega: f64,
    duration: f64,
}

// A helper struct for the overall spin commands message.
#[derive(Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct SpinCommandsHelper {
    commands: Vec<SpinCommandHelper>,
    period: f64,
}

#[derive(Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct PosePositionHelper {
    x: f64,
    y: f64,
    z: f64
}
#[derive(Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct PoseOrientationHelper {
    x: f64,
    y: f64,
    z: f64,
    w: f64
}
#[derive(Deserialize, Debug)]
#[serde(deny_unknown_fields)]
struct PoseHelper {
    position: PosePositionHelper,
    orientation: PoseOrientationHelper
}


// Convert the helper into the actual ROS message type.
impl TryFrom<SpinCommandsHelper> for MSpinCommands {
    type Error = &'static str;

    fn try_from(helper: SpinCommandsHelper) -> Result<Self, Self::Error> {
        Ok(MSpinCommands {
            commands: helper
                .commands
                .into_iter()
                .map(|cmd| r2r::spin_interfaces::msg::SpinCommand {
                    omega: cmd.omega,
                    duration: cmd.duration,
                })
                .collect(),
            period: helper.period,
        })
    }
}

// Convert the helper into the actual ROS message type.
impl TryFrom<PoseHelper> for MPoseStamped {
    type Error = &'static str;

    fn try_from(helper: PoseHelper) -> Result<Self, Self::Error> {
        match std::time::SystemTime::now().duration_since(std::time::SystemTime::UNIX_EPOCH) {
            Ok(n) => Ok(MPoseStamped {
                header: r2r::std_msgs::msg::Header {
                    stamp: Time {
                        sec: if n.as_secs() <= (std::i32::MAX as u64) {
                            n.as_secs() as i32
                        } else {
                            panic!("timestamp from SystemTime overflows i32")
                        },
                        nanosec: n.subsec_nanos()
                    },
                    frame_id: "map".to_string()
                },
                pose: r2r::geometry_msgs::msg::Pose {
                    position: r2r::geometry_msgs::msg::Point {
                        x: helper.position.x,
                        y: helper.position.y,
                        z: helper.position.z
                    },
                    orientation: r2r::geometry_msgs::msg::Quaternion {
                        x: helper.orientation.x,
                        y: helper.orientation.y,
                        z: helper.orientation.z,
                        w: helper.orientation.w,
                    }
                }
            }),
            Err(_) => panic!("SystemTime before UNIX EPOCH!"),
        }
    }
}

#[derive(Debug, Clone)]
enum MQTT2ROSError {
    InvalidTopic,
    DeserializationError(serde_json5::Error),
}

impl TryFrom<Message> for MQTT2ROSData {
    type Error = MQTT2ROSError;

    fn try_from(msg: Message) -> Result<Self, Self::Error> {
        if msg.topic() == SPIN_TOPIC.mqtt_name {
            match serde_json5::from_str::<MQTT2ROSData>(&msg.payload_str()) {
                Ok(msg) => Ok(msg),
                Err(e) => Err(MQTT2ROSError::DeserializationError(e)),
            }
        } else if msg.topic() == GOAL_TOPIC.mqtt_name {
            match serde_json5::from_str::<MQTT2ROSData>(&msg.payload_str()) {
                Ok(msg) => Ok(msg),
                Err(e) => Err(MQTT2ROSError::DeserializationError(e)),
            }
        } else {
            Err(MQTT2ROSError::InvalidTopic)
        }
    }
}

#[instrument(level=tracing::Level::DEBUG)]
pub async fn create_mqtt_client(hostname: String) -> Result<mqtt::AsyncClient, mqtt::Error> {
    let create_opts = mqtt::CreateOptionsBuilder::new_v3()
        .server_uri(hostname.clone())
        .client_id(format!("robosapiens_ros2mqttbridge_{}", Uuid::new_v4()))
        .finalize();

    let connect_opts = mqtt::ConnectOptionsBuilder::new_v3()
        .keep_alive_interval(Duration::from_secs(30))
        .clean_session(false)
        .finalize();

    let mqtt_client = mqtt::AsyncClient::new(create_opts)?;

    debug!(
        name = "Created MQTT client",
        ?hostname,
        client_id = mqtt_client.client_id()
    );

    // Try to connect to the broker
    loop {
        match mqtt_client.clone().connect(connect_opts.clone()).await {
            Ok(_) => {
                info!("Connected to MQTT broker");
                return Ok(mqtt_client);
            }
            Err(e) => {
                warn!(?e, "Failed to connect to MQTT broker; retrying in 1 second");
                tokio::time::sleep(Duration::from_secs(1)).await;
            }
        }
    }
}

async fn mqtt_client_actor(
    mqtt_hostname: &str,
    topics: Vec<&str>,
) -> Result<
    (
        // Subscription stream
        BoxStream<'static, Option<Message>>,
        // Stream to send mqtt messages and get responses
        tokio::sync::mpsc::Sender<(oneshot::Sender<Option<mqtt::Error>>, Message)>,
        // Future marking the end of the actor
        impl std::future::Future<Output = ()> + Send,
    ),
    mqtt::Error,
> {
    let mut mqtt_client = create_mqtt_client(mqtt_hostname.to_string()).await?;

    let stream = mqtt_client.get_stream(25);

    let (sender, mut receiver) =
        tokio::sync::mpsc::channel::<(oneshot::Sender<Option<mqtt::Error>>, Message)>(10);

    mqtt_client
        .subscribe_many_same_qos(&topics, MQTT_QOS)
        .await?;

    let fut = async move {
        while let Some((tx, msg)) = receiver.recv().await {
            let publish_result = match mqtt_client.publish(msg).await {
                Ok(_) => None,
                Err(e) => Some(e),
            };
            if let Err(_e) = tx.send(publish_result) {
                info!("MQTT clients have been dropped; shutting down");
                break;
            }
        }
    };

    Ok((Box::pin(stream), sender, fut))
}

async fn ros_node_actor(
    ros_namespace: &str,
) -> Result<
    (
        // Subscription stream
        BoxStream<'static, r2r::sensor_msgs::msg::LaserScan>,
        BoxStream<'static, r2r::geometry_msgs::msg::Twist>,
        BoxStream<'static, r2r::geometry_msgs::msg::Twist>,
        BoxStream<'static, r2r::nav_msgs::msg::Odometry>,
        // Spin command publisher
        Publisher<MSpinCommands>,
        Publisher<MPoseStamped>,
        // Future marking the end of the actor
        impl std::future::Future<Output = ()> + Send,
    ),
    r2r::Error,
> {
    let context = r2r::Context::create()?;
    let mut node = r2r::Node::create(
        context,
        format!("robosapiens_rosmqttbridge_{}", Uuid::new_v4().as_simple()).as_str(),
        ros_namespace,
    )?;

    let sensor_qos = QosProfile {
        // Keep last 5 messages, typical for sensor data
        history: QosHistoryPolicy::KeepLast,
        // Set depth to 5
        depth: 5,
        // Allow best effort delivery for low-latency sensor data
        reliability: QosReliabilityPolicy::BestEffort,
        // Volatile durability since historical data is not required
        durability: QosDurabilityPolicy::Volatile,

        deadline: QosProfile::default().deadline,
        lifespan: QosProfile::default().lifespan,
        liveliness: QosProfile::default().liveliness,
        liveliness_lease_duration: QosProfile::default().liveliness_lease_duration,
        avoid_ros_namespace_conventions: false,
    };

    debug!("Subscribing to scan safe");
    let sub_laser = node
        .subscribe::<r2r::sensor_msgs::msg::LaserScan>(SCAN_TOPIC.ros_name, sensor_qos.clone())?;
    let sub_vel = node
        .subscribe::<r2r::geometry_msgs::msg::Twist>(VELOCITY_TOPIC.ros_name, sensor_qos.clone())?;
    let sub_mon = node
        .subscribe::<r2r::geometry_msgs::msg::Twist>(COLLISION_TOPIC.ros_name, sensor_qos.clone())?;
    let sub_odom = node
        .subscribe::<r2r::nav_msgs::msg::Odometry>(ODOM_TOPIC.ros_name, sensor_qos.clone())?; 
    debug!("Subscribed to scan safe");

    let pub_spin =
        node.create_publisher::<MSpinCommands>(SPIN_TOPIC.ros_name, QosProfile::default())?;
    let pub_goal =
        node.create_publisher::<MPoseStamped>(GOAL_TOPIC.ros_name, QosProfile::default())?;

    let fut = async move {
        loop {
            debug!("Spinning ROS node");
            tokio::time::sleep(std::time::Duration::from_millis(100)).await;
            node.spin_once(std::time::Duration::from_millis(10));
        }
    };

    Ok((Box::pin(sub_laser), Box::pin(sub_vel), Box::pin(sub_mon), Box::pin(sub_odom), pub_spin, pub_goal, fut))
}

// Duplicate for additional ROS streams in separate loop
#[instrument(level=tracing::Level::DEBUG, skip(ros_stream, mqtt_sender))]
async fn ros_to_mqtt_laser(
    mut ros_stream: BoxStream<'static, r2r::sensor_msgs::msg::LaserScan>,
    mqtt_sender: &tokio::sync::mpsc::Sender<(oneshot::Sender<Option<mqtt::Error>>, Message)>,
) {
    info!("Starting ROS to MQTT bridge");
    while let Some(msg) = ros_stream.next().await {
        debug!("Received ROS message");
        // let _span = tracing::info_span!("Sending ROS message to MQTT", ?msg).entered();

        let topic = SCAN_TOPIC;

        let serialized_msg = match serde_json5::to_string(&msg) {
            Ok(msg) => msg,
            Err(e) => {
                error!(?e, "Failed to JSON serialize message for MQTT");
                continue;
            }
        };

        let mqtt_msg = mqtt::Message::new(topic.mqtt_name, serialized_msg, MQTT_QOS);

        let (tx, rx) = oneshot::channel();
        mqtt_sender.send((tx, mqtt_msg)).await.unwrap();
        info!("[ROS->MQTT] Forwarded LaserScan message");
        debug!("LaserScan: {:?}", msg);

        if let Some(e) = rx.await.unwrap() {
            error!(?e, "Failed to publish MQTT message");
            // TODO: should this be a break
        }
    }

    info!("Laser scan input stream ended; shutting down");
}

#[instrument(level=tracing::Level::DEBUG, skip(ros_stream, mqtt_sender))]
async fn ros_to_mqtt_vel(
    mut ros_stream: BoxStream<'static, r2r::geometry_msgs::msg::Twist>,
    mqtt_sender: &tokio::sync::mpsc::Sender<(oneshot::Sender<Option<mqtt::Error>>, Message)>,
) {
    info!("Starting ROS to MQTT bridge");
    while let Some(msg) = ros_stream.next().await {
        debug!("Received ROS message");
        // let _span = tracing::info_span!("Sending ROS message to MQTT", ?msg).entered();

        let topic = VELOCITY_TOPIC;

        let serialized_msg = match serde_json5::to_string(&msg) {
            Ok(msg) => msg,
            Err(e) => {
                error!(?e, "Failed to JSON serialize message for MQTT");
                continue;
            }
        };

        let mqtt_msg = mqtt::Message::new(topic.mqtt_name, serialized_msg, MQTT_QOS);

        let (tx, rx) = oneshot::channel();
        mqtt_sender.send((tx, mqtt_msg)).await.unwrap();
        info!("[ROS->MQTT] Forwarded Velocity message");
        debug!("Velocity: {:?}", msg);

        if let Some(e) = rx.await.unwrap() {
            error!(?e, "Failed to publish velocity MQTT message");
            // TODO: should this be a break
        }

        let mut x_topic = topic.mqtt_name.to_owned();
        x_topic.push_str("LinearX"); 
        let mqtt_msg = mqtt::Message::new(x_topic, msg.linear.x.to_string(), MQTT_QOS);
        let (tx, rx) = oneshot::channel();
        mqtt_sender.send((tx, mqtt_msg)).await.unwrap();
        debug!("Velocity: {:?}", msg);

        if let Some(e) = rx.await.unwrap() {
            error!(?e, "Failed to publish velocity MQTT message LX");
            // TODO: should this be a break
        }

        let mut z_topic = topic.mqtt_name.to_owned();
        z_topic.push_str("AngularZ"); 
        let mqtt_msg = mqtt::Message::new(z_topic, msg.angular.z.to_string(), MQTT_QOS);
        let (tx, rx) = oneshot::channel();
        mqtt_sender.send((tx, mqtt_msg)).await.unwrap();

        if let Some(e) = rx.await.unwrap() {
            error!(?e, "Failed to publish velocity MQTT message AZ");
            // TODO: should this be a break
        }
    }

    info!("Velocity input stream ended; shutting down");
}

#[instrument(level=tracing::Level::DEBUG, skip(ros_stream, mqtt_sender))]
async fn ros_to_mqtt_mon(
    mut ros_stream: BoxStream<'static, r2r::geometry_msgs::msg::Twist>,
    mqtt_sender: &tokio::sync::mpsc::Sender<(oneshot::Sender<Option<mqtt::Error>>, Message)>,
) {
    info!("Starting ROS to MQTT bridge");
    while let Some(msg) = ros_stream.next().await {
        debug!("Received ROS message");
        // let _span = tracing::info_span!("Sending ROS message to MQTT", ?msg).entered();

        let topic = COLLISION_TOPIC;

        let serialized_msg = match serde_json5::to_string(&msg) {
            Ok(msg) => msg,
            Err(e) => {
                error!(?e, "Failed to JSON serialize message for MQTT");
                continue;
            }
        };

        let mqtt_msg = mqtt::Message::new(topic.mqtt_name, serialized_msg, MQTT_QOS);

        let (tx, rx) = oneshot::channel();
        mqtt_sender.send((tx, mqtt_msg)).await.unwrap();
        info!("[ROS->MQTT] Forwarded Collision monitor's Velocity message");
        debug!(" Collision monitor's Velocity: {:?}", msg);

        if let Some(e) = rx.await.unwrap() {
            error!(?e, "Failed to publish collision MQTT message");
            // TODO: should this be a break
        }

        let mut x_topic = topic.mqtt_name.to_owned();
        x_topic.push_str("LinearX"); 
        let mqtt_msg = mqtt::Message::new(x_topic, msg.linear.x.to_string(), MQTT_QOS);
        let (tx, rx) = oneshot::channel();
        mqtt_sender.send((tx, mqtt_msg)).await.unwrap();
        debug!("Velocity: {:?}", msg);

        if let Some(e) = rx.await.unwrap() {
            error!(?e, "Failed to publish collision MQTT message LX");
            // TODO: should this be a break
        }

        let mut z_topic = topic.mqtt_name.to_owned();
        z_topic.push_str("AngularZ"); 
        let mqtt_msg = mqtt::Message::new(z_topic, msg.angular.z.to_string(), MQTT_QOS);
        let (tx, rx) = oneshot::channel();
        mqtt_sender.send((tx, mqtt_msg)).await.unwrap();

        if let Some(e) = rx.await.unwrap() {
            error!(?e, "Failed to publish collision MQTT message AZ");
            // TODO: should this be a break
        }
    }

    info!(" Collision monitor velocity input stream ended; shutting down");
}

#[instrument(level=tracing::Level::DEBUG, skip(ros_stream, mqtt_sender))]
async fn ros_to_mqtt_odom(
    mut ros_stream: BoxStream<'static, r2r::nav_msgs::msg::Odometry>,
    mqtt_sender: &tokio::sync::mpsc::Sender<(oneshot::Sender<Option<mqtt::Error>>, Message)>,
) {
    info!("Starting ROS to MQTT bridge");
    while let Some(msg) = ros_stream.next().await {
        debug!("Received Odom ROS message");
        // let _span = tracing::info_span!("Sending ROS message to MQTT", ?msg).entered();

        let topic = ODOM_TOPIC;

        let pos_x =  &msg.pose.pose.position.x;
        let pos_y =  &msg.pose.pose.position.y;
        let angle_qz =  &msg.pose.pose.orientation.z.asin()*2.;
        let angle_qw =  &msg.pose.pose.orientation.w.acos()*2.;
        let angle_z = if angle_qw > PI {-angle_qz} else {angle_qz};

        // let serialized_msg = format!("{\"x\":{},\"y\":{},\"angle\":{}}", pos_x, pos_y, angle_z);
        // Valid list format: {"List": [{"Int": 1}, {"Float": 2.5}]}
        let serialized_msg = format!("{{\"List\":[{{\"Float\":{}}},{{\"Float\":{}}},{{\"Float\":{}}}]}}", pos_x, pos_y, angle_z);

        let mqtt_msg = mqtt::Message::new(topic.mqtt_name, serialized_msg, MQTT_QOS);


        let (tx, rx) = oneshot::channel();
        mqtt_sender.send((tx, mqtt_msg)).await.unwrap();
        info!("[ROS->MQTT] Forwarded Odom message");
        debug!("Odom: {:?}", msg);

        if let Some(e) = rx.await.unwrap() {
            error!(?e, "Failed to publish Odom MQTT message");
            // TODO: should this be a break
        }
    }

    info!("Odom input stream ended; shutting down");
}

#[instrument(level=tracing::Level::DEBUG, skip(mqtt_stream, ros_spin_publisher, ros_goal_publisher))]
async fn mqtt_to_ros(
    mut mqtt_stream: BoxStream<'static, Option<Message>>,
    ros_spin_publisher: Publisher<MSpinCommands>,
    ros_goal_publisher: Publisher<MPoseStamped>,
) {
    info!("Starting MQTT to ROS bridge");
    while let Some(Some(msg)) = mqtt_stream.next().await {
        // let _span = tracing::info_span!("Received MQTT message", ?msg).entered();

        let payload: String = msg.payload_str().to_string();
        let data = match MQTT2ROSData::try_from(msg) {
            Ok(msg) => msg,
            Err(MQTT2ROSError::InvalidTopic) => {
                error!("Received message on invalid topic; ignoring");
                continue;
            }
            Err(MQTT2ROSError::DeserializationError(e)) => {
                error!(
                    ?e,
                    "Failed to deserialize MQTT message; ignoring\nPayload: {}", payload
                );
                continue;
            }
        };

        match data {
            MQTT2ROSData::SpinCommands(msg) => {
                ros_spin_publisher.publish(&msg).unwrap();
                info!("[MQTT->ROS] Forwarded SpinCommands message");
                debug!("SpinCommands: {:?}", msg);
            },
            MQTT2ROSData::PoseStamped(msg) => {
                ros_goal_publisher.publish(&msg).unwrap();
                info!("[MQTT->ROS] Forwarded GoalPose message");
                debug!("GoalPose: {:?}", msg);
            }
        }
    }

    info!("MQTT input stream ended; shutting down");
}

pub async fn bridge(
    mqtt_hostname: &str,
    ros_namespace: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    debug!("Starting bridge");
    let (ros_stream_laser, 
        ros_stream_velocity,
        ros_stream_monitor,
        ros_stream_odom,
        ros_publisher_spin, 
        ros_publisher_goal, 
        ros_fut) = ros_node_actor(ros_namespace).await.unwrap();
    let (mqtt_stream, mqtt_sender, mqtt_fut) =
        mqtt_client_actor(mqtt_hostname, vec![SPIN_TOPIC.mqtt_name, GOAL_TOPIC.mqtt_name]).await?;
    let ros_to_mqtt_laser_fut = ros_to_mqtt_laser(ros_stream_laser, &mqtt_sender);
    let ros_to_mqtt_vel_fut = ros_to_mqtt_vel(ros_stream_velocity, &mqtt_sender);
    let ros_to_mqtt_mon_fut = ros_to_mqtt_mon(ros_stream_monitor, &mqtt_sender);
    let ros_to_mqtt_odom_fut = ros_to_mqtt_odom(ros_stream_odom, &mqtt_sender);
    let mqtt_to_ros_fut = mqtt_to_ros(mqtt_stream, ros_publisher_spin, ros_publisher_goal);
    // let blocking_ros_fut = tokio::task::spawn_blocking(|| ros_fut);

    debug!("Entering select on futures");

    Ok(select! {
        _ = ros_to_mqtt_laser_fut => (),
        _ = ros_to_mqtt_vel_fut => (),
        _ = ros_to_mqtt_mon_fut => (),
        _ = ros_to_mqtt_odom_fut => (),
        _ = mqtt_to_ros_fut => (),
        _ = ros_fut => (),
        _ = mqtt_fut => (),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use test_log::test;
    #[test]
    fn test_convert_valid_spin_commands() {
        let msg = r#"{"commands":[],"period":0.0}"#;
        let mqtt_msg = mqtt::Message::new(SPIN_TOPIC.mqtt_name, msg.to_string(), MQTT_QOS);
        let result = MQTT2ROSData::try_from(mqtt_msg);
        assert!(result.is_ok());
    }

    #[test]
    fn test_invalid_spin_commands() {
        let msg = r#"{"blah": false}"#;
        let mqtt_msg = mqtt::Message::new(SPIN_TOPIC.mqtt_name, msg.to_string(), MQTT_QOS);
        let result = MQTT2ROSData::try_from(mqtt_msg);
        if let Ok(res) = result.clone() {
            info!("{:?}", res);
        }
        assert!(result.is_err());
    }

    #[test]
    fn test_invalid_spin_commands_extra_fields() {
        let msg = r#"{"commands":[],"period":0.0, "blah": false}"#;
        let mqtt_msg = mqtt::Message::new(SPIN_TOPIC.mqtt_name, msg.to_string(), MQTT_QOS);
        let result = MQTT2ROSData::try_from(mqtt_msg);
        if let Ok(res) = result.clone() {
            info!("{:?}", res);
        }
        assert!(result.is_err());
    }
}
