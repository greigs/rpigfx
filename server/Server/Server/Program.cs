using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class SynchronousSocketListener
{

    // Incoming data from the client.
    public static string data = null;
    public static Stack<string> stack = new Stack<string>();


    public static void StartListening()
    {
        // Data buffer for incoming data.
        byte[] bytes = new Byte[1024];

        // Establish the local endpoint for the socket.
        // Dns.GetHostName returns the name of the 
        // host running the application.
        IPHostEntry ipHostInfo = Dns.Resolve(Dns.GetHostName());
        IPAddress ipAddress = ipHostInfo.AddressList[0];
        IPEndPoint localEndPoint = new IPEndPoint(ipAddress, 1024);

        // Create a TCP/IP socket.
        Socket listener = new Socket(AddressFamily.InterNetwork,
            SocketType.Stream, ProtocolType.Tcp);

        // Bind the socket to the local endpoint and 
        // listen for incoming connections.
        try
        {
            listener.Bind(localEndPoint);
            listener.Listen(10);

            // Start listening for connections.
            while (true)
            {
                Console.WriteLine("Waiting for a connection...");
                // Program is suspended while waiting for an incoming connection.
                Socket handler = listener.Accept();



                // An incoming connection needs to be processed.
                while (true)
                {
                    try
                    {
                        bool found = false;
                        while (!found)
                        {
                            bytes = new byte[1024];
                            int bytesRec = handler.Receive(bytes);
                            data += Encoding.ASCII.GetString(bytes, 0, bytesRec);
                            if (data.IndexOf("|") > -1)
                            {
                                found = true;
                            }
                        }

                        Console.WriteLine("Text received : {0}", data);


                        while (stack.Count == 0)
                        {
                            Thread.Sleep(10);
                        }
                        var response = stack.Pop();
                        byte[] msg = Encoding.ASCII.GetBytes(response);

                        handler.Send(msg);

                    }
                    catch (SocketException socketException)
                    {
                        Console.WriteLine("Client closed the socket");
                        handler.Shutdown(SocketShutdown.Both);
                        handler.Close();
                        handler = listener.Accept();
                    }


                    data = null;

                }
 

                handler.Shutdown(SocketShutdown.Both);
                handler.Close();

                // Show the data on the console.


   

            }

        }
        catch (Exception e)
        {
            Console.WriteLine(e.ToString());
        }

        Console.WriteLine("\nPress ENTER to continue...");
        Console.Read();

    }

    public static void Main(String[] args)
    {
        var threadStart = new ThreadStart(StartListening);
        var t = new Thread(threadStart);
        t.Start();
        
            var dumpdata = new ThreadStart(DumpData);
            var tdump = new Thread(dumpdata);
            tdump.Start();
        t.Join();
    }

    private static void DumpData()
    {
        while (true)
        {
            Thread.Sleep(10);
            stack.Push(DateTime.Now.Ticks.ToString());
        }

    }
}