//Do not edit! This file was generated by Unity-ROS MessageGeneration.
using System;
using System.Linq;
using System.Collections.Generic;
using System.Text;
using Unity.Robotics.ROSTCPConnector.MessageGeneration;

namespace RosMessageTypes.ROS
{
    [Serializable]
    public class Point32Msg : Message
    {
        public const string k_RosMessageName = "ROS/Point32";
        public override string RosMessageName => k_RosMessageName;

        //  This contains the position of a point in free space(with 32 bits of precision).
        //  It is recommeded to use Point wherever possible instead of Point32.  
        //  
        //  This recommendation is to promote interoperability.  
        // 
        //  This message is designed to take up less space when sending
        //  lots of points at once, as in the case of a PointCloud.  
        public float x;
        public float y;
        public float z;

        public Point32Msg()
        {
            this.x = 0.0f;
            this.y = 0.0f;
            this.z = 0.0f;
        }

        public Point32Msg(float x, float y, float z)
        {
            this.x = x;
            this.y = y;
            this.z = z;
        }

        public static Point32Msg Deserialize(MessageDeserializer deserializer) => new Point32Msg(deserializer);

        private Point32Msg(MessageDeserializer deserializer)
        {
            deserializer.Read(out this.x);
            deserializer.Read(out this.y);
            deserializer.Read(out this.z);
        }

        public override void SerializeTo(MessageSerializer serializer)
        {
            serializer.Write(this.x);
            serializer.Write(this.y);
            serializer.Write(this.z);
        }

        public override string ToString()
        {
            return "Point32Msg: " +
            "\nx: " + x.ToString() +
            "\ny: " + y.ToString() +
            "\nz: " + z.ToString();
        }

#if UNITY_EDITOR
        [UnityEditor.InitializeOnLoadMethod]
#else
        [UnityEngine.RuntimeInitializeOnLoadMethod]
#endif
        public static void Register()
        {
            MessageRegistry.Register(k_RosMessageName, Deserialize);
        }
    }
}
