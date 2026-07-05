using AssetRipper.GUI.Web;

namespace UnityAssetExtractor
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length < 2)
            {
                Console.WriteLine("Usage: UnityAssetExtractor <inputPath> <outputProjectPath>");
                return;
            }

            string inputPath = args[0];
            string outputProjectPath = args[1];

            string[] filesToLoad;

            if (Directory.Exists(inputPath))
            {
                // مجلد كامل: نجمع كل الملفات بداخله (بما فيها المتفرعة) كمدخلات
                filesToLoad = Directory.GetFiles(inputPath, "*", SearchOption.AllDirectories);
                Console.WriteLine($"وجدت {filesToLoad.Length} ملف داخل المجلد: {inputPath}");
            }
            else if (File.Exists(inputPath))
            {
                filesToLoad = new[] { inputPath };
            }
            else
            {
                Console.WriteLine($"لا يوجد ملف أو مجلد بهذا المسار: {inputPath}");
                return;
            }

            try
            {
                GameFileLoader.LoadAndProcess(filesToLoad);
                GameFileLoader.ExportUnityProject(outputProjectPath);
                Console.WriteLine($"تم الاستخراج بنجاح إلى: {outputProjectPath}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"حدث خطأ: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
            }
        }
    }
}
